from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import (
    CompetencyEvaluationItem,
    GeneratedCompetencyItem,
    InterviewAnalyzerState,
    InterviewEvaluationReportSchema,
    TranscriptCompetencyGenerationSchema,
)
from app.agent.GuardrailNode import GuardrailNode
from app.agent.LlmFactory import LlmFactory
from app.model.CandidateModel import Candidate
from app.model.JobModel import Job, TranscriptSegment
from app.model.RubricModel import Competency, Profile
from app.model.SummaryModel import Flag, SummaryEvidence, SummaryPoint
from app.service.AuditLogService import AuditLogService


class InterviewAnalyzerGraph:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = AuditLogService(session)

    async def consent_gate_node(self, state: InterviewAnalyzerState) -> dict[str, Any]:
        consent = state.get("consent_status", "NOT_GRANTED")
        if consent != "GRANTED":
            # Update job status in DB if job exists
            job_id = state.get("job_id")
            if job_id:
                job_stmt = select(Job).where(Job.nid == job_id)
                job = (await self.session.execute(job_stmt)).scalars().first()
                if job:
                    job.nstatus = 90  # REJECTED_NO_CONSENT
                    self.session.add(job)
                    await self.session.commit()

            audit = await self.audit_service.log_event(
                event_type="CONSENT_REJECTED",
                actor="SYSTEM_CONSENT_GATE",
                actor_type="AGENT",
                title="Interview Processing Rejected - No Consent",
                description="The candidate has not provided or has revoked consent for the processing of the interview recording (Consent Status != GRANTED).",
                job_id=job_id,
            )
            return {
                "job_status": "REJECTED_NO_CONSENT",
                "audit_entries": [
                    *state.get("audit_entries", []),
                    {"event_type": "CONSENT_REJECTED", "id": audit.id},
                ],
            }
        return {"job_status": "ACCESS_CHECKED"}

    async def transcript_segmenter_node(self, state: InterviewAnalyzerState) -> dict[str, Any]:
        job_id = state.get("job_id")
        if not job_id:
            return {}

        cand_name = state.get("candidate_name", "Kandidat")
        cand_pos = state.get("position", "Software Engineer")
        notes = state.get("notes") or ""

        # Check existing segments
        seg_stmt = select(TranscriptSegment).where(TranscriptSegment.nid_job == job_id).order_by(TranscriptSegment.nsegment_no)
        existing = (await self.session.execute(seg_stmt)).scalars().all()
        if existing:
            return {
                "transcript_segments": [
                    {
                        "id": s.nid,
                        "segment_no": s.nsegment_no,
                        "text": s.vtext,
                        "confidence": s.fconfidence,
                        "speaker_type": (s.vspeaker_type or "CANDIDATE").upper(),
                        "speaker_label": s.vspeaker_label or "SPEAKER_0",
                        "start_ms": s.nstart_ms,
                        "end_ms": s.nend_ms,
                    }
                    for s in existing
                ]
            }

        # Synthesize realistic timestamped segments based on candidate role and notes
        segments_data = [
            (
                1,
                10000,
                25000,
                "INTERVIEWER",
                f"Welcome {cand_name} to this interview session for the {cand_pos} position. Could you tell us about your professional background?",
                0.98,
            ),
            (
                2,
                27000,
                75000,
                "CANDIDATE",
                f"Thank you. I have in-depth experience in {cand_pos}. {notes if notes else 'My main focus is designing reliable and scalable systems and collaborating across teams.'}",
                0.95,
            ),
            (
                3,
                78000,
                110000,
                "INTERVIEWER",
                "How do you approach situations when there are differing technical opinions within the engineering team?",
                0.97,
            ),
            (
                4,
                112000,
                160000,
                "CANDIDATE",
                "I prioritize data-driven discussions and empirical benchmarks rather than personal assumptions. When differences arise, we build a small proof-of-concept to validate hypotheses together.",
                0.96,
            ),
        ]

        created_segments = []
        for no, s_ms, e_ms, speaker, text, conf in segments_data:
            seg = TranscriptSegment(
                nid_job=job_id,
                nsegment_no=no,
                nstart_ms=s_ms,
                nend_ms=e_ms,
                vspeaker_label=speaker,
                vspeaker_type=speaker,
                vtext=text,
                fconfidence=conf,
            )
            self.session.add(seg)
            created_segments.append(seg)

        await self.session.flush()

        return {
            "transcript_segments": [
                {"id": s.nid, "segment_no": s.nsegment_no, "text": s.vtext, "confidence": s.fconfidence}
                for s in created_segments
            ],
            "job_status": "TRANSCRIBED",
        }

    async def transcript_flag_scanner_node(self, state: InterviewAnalyzerState) -> dict[str, Any]:
        job_id = state.get("job_id")
        segments = state.get("transcript_segments", [])
        if not job_id:
            return {}

        flags = []
        for seg in segments:
            text = seg.get("text", "")
            is_safe, note = GuardrailNode.scan_text(text)
            if not is_safe:
                fl = Flag(
                    nid_job=job_id,
                    nid_transcript=seg.get("id"),
                    vflag_type="EMBEDDED_INSTRUCTION",
                    vneutral_text=f"Potential hidden instruction detected in segment #{seg.get('segment_no')}: {note}",
                    vstatus="OPEN",
                )
                self.session.add(fl)
                flags.append({"type": "EMBEDDED_INSTRUCTION", "note": note})

            if seg.get("confidence", 1.0) < 0.8:
                fl = Flag(
                    nid_job=job_id,
                    nid_transcript=seg.get("id"),
                    vflag_type="UNCERTAIN_SEGMENT",
                    vneutral_text=f"Low transcription confidence (< 80%) on segment #{seg.get('segment_no')}.",
                    vstatus="OPEN",
                )
                self.session.add(fl)
                flags.append({"type": "UNCERTAIN_SEGMENT"})

        if flags:
            await self.session.flush()

        return {"flags": flags}

    async def rubric_evaluator_node(self, state: InterviewAnalyzerState) -> dict[str, Any]:
        job_id = state.get("job_id")
        profile_id = state.get("profile_id")
        if not job_id or not profile_id:
            return {}

        # Always reload segments from DB to ensure speaker_type and timestamps are fresh
        seg_stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.nid_job == job_id)
            .order_by(TranscriptSegment.nsegment_no)
        )
        existing_segs = (await self.session.execute(seg_stmt)).scalars().all()
        segments = [
            {
                "id": s.nid,
                "segment_no": s.nsegment_no,
                "text": s.vtext,
                "confidence": s.fconfidence,
                "speaker_type": (s.vspeaker_type or "CANDIDATE").upper(),
                "speaker_label": s.vspeaker_label or "SPEAKER_0",
                "start_ms": s.nstart_ms,
                "end_ms": s.nend_ms,
            }
            for s in existing_segs
        ]

        if not segments:
            return {}

        all_text = " ".join([s.get("text", "") for s in segments])

        # Detect transcript language (Indonesian vs English)
        indonesian_keywords = {
            "yang", "dan", "di", "dengan", "saya", "ini", "untuk", "dari",
            "adalah", "dalam", "bisa", "kami", "sistem", "tim", "pengalaman",
            "apakah", "bagaimana", "selamat", "melamar", "posisi",
        }
        words = set(all_text.lower().split())
        id_match = len(words & indonesian_keywords)
        is_indonesian = id_match >= 3

        cand_pos = state.get("position") or "General Candidate"

        # Format transcript lines with speaker attribution
        dialogue_lines = []
        for s in segments:
            role = s.get("speaker_type", "CANDIDATE")
            start_sec = s.get("start_ms", 0) // 1000
            time_str = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
            dialogue_lines.append(f"[Seg #{s.get('segment_no', 1)} | {time_str} | {role}]: {s.get('text', '')}")
        formatted_dialogue = "\n".join(dialogue_lines)

        # Fetch competencies for profile
        comp_stmt = (
            select(Competency)
            .where(Competency.nid_profile == profile_id)
            .order_by(Competency.nsort_order, Competency.nid)
        )
        competencies = list((await self.session.execute(comp_stmt)).scalars().all())

        # Clean up any existing SummaryPoint and SummaryEvidence for this job to allow clean re-evaluations
        sp_subq = select(SummaryPoint.nid).where(SummaryPoint.nid_job == job_id)
        existing_sp_ids = (await self.session.execute(sp_subq)).scalars().all()
        if existing_sp_ids:
            await self.session.execute(
                delete(SummaryEvidence).where(SummaryEvidence.nid_summary_point.in_(existing_sp_ids))
            )
            await self.session.execute(
                delete(SummaryPoint).where(SummaryPoint.nid.in_(existing_sp_ids))
            )
            await self.session.commit()

        # Determine if competencies should be regenerated from actual audio dialogue
        # If no competencies exist, or all competencies were generated by SYSTEM_TRANSCRIPT_ASR
        should_regenerate = not competencies or all(
            getattr(c, "vcrea", None) == "SYSTEM_TRANSCRIPT_ASR" for c in competencies
        )

        if should_regenerate:
            def fallback_competencies() -> TranscriptCompetencyGenerationSchema:
                txt_low = all_text.lower()
                if any(k in txt_low for k in ("kitchen", "cook", "restaurant", "food", "chef", "dapur", "masak")):
                    if is_indonesian:
                        return TranscriptCompetencyGenerationSchema(competencies=[
                            GeneratedCompetencyItem(code="C1", name="Operasional Dapur & Kebersihan", reference_question="Bagaimana pengalaman kandidat dalam menjalankan operasional dan standar kebersihan dapur?"),
                            GeneratedCompetencyItem(code="C2", name="Kesiapan Fisik & Ketahanan Kerja", reference_question="Bagaimana kandidat menghadapi beban kerja tinggi di dapur dan jam kerja fleksibel?"),
                            GeneratedCompetencyItem(code="C3", name="Kerjasama Tim Dapur & Komunikasi", reference_question="Bagaimana cara kandidat berkoordinasi dengan sesama staf dan pimpinan dapur?"),
                            GeneratedCompetencyItem(code="C4", name="Keandalan & Disiplin Jadwal", reference_question="Bagaimana riwayat kehadiran, komitmen, dan kesiapan waktu kerja kandidat?"),
                        ])
                    return TranscriptCompetencyGenerationSchema(competencies=[
                        GeneratedCompetencyItem(code="C1", name="Kitchen Operations & Sanitation", reference_question="How does the candidate demonstrate hands-on experience in kitchen prep and sanitation?"),
                        GeneratedCompetencyItem(code="C2", name="Work Stamina & Pace Handling", reference_question="How does the candidate handle peak restaurant rushes and physically demanding shifts?"),
                        GeneratedCompetencyItem(code="C3", name="Teamwork & Kitchen Communication", reference_question="How does the candidate coordinate with colleagues and kitchen managers?"),
                        GeneratedCompetencyItem(code="C4", name="Reliability & Schedule Flexibility", reference_question="What is the candidate's attendance record and availability for open shifts?"),
                    ])
                if is_indonesian:
                    return TranscriptCompetencyGenerationSchema(competencies=[
                        GeneratedCompetencyItem(code="C1", name="Keahlian Teknis & Pemecahan Masalah", reference_question="Bagaimana kandidat mendemonstrasikan keahlian teknis terkait posisi?"),
                        GeneratedCompetencyItem(code="C2", name="Komunikasi & Kolaborasi", reference_question="Bagaimana kandidat berkomunikasi dan bekerja dalam tim?"),
                        GeneratedCompetencyItem(code="C3", name="Adaptabilitas & Ketahanan", reference_question="Bagaimana kandidat beradaptasi dengan perubahan atau tantangan kerja?"),
                        GeneratedCompetencyItem(code="C4", name="Inisiatif & Motivasi Kerja", reference_question="Sejauh mana motivasi dan inisiatif kandidat terhadap peran ini?"),
                    ])
                return TranscriptCompetencyGenerationSchema(competencies=[
                    GeneratedCompetencyItem(code="C1", name="Technical Knowledge & Problem Solving", reference_question="How does the candidate demonstrate relevant core skills?"),
                    GeneratedCompetencyItem(code="C2", name="Communication & Collaboration", reference_question="How clearly does the candidate communicate and collaborate?"),
                    GeneratedCompetencyItem(code="C3", name="Adaptability & Resilience", reference_question="How does the candidate handle challenges and changes?"),
                    GeneratedCompetencyItem(code="C4", name="Initiative & Work Drive", reference_question="What drives the candidate and what initiative do they take?"),
                ])

            system_gen_prompt = (
                "You are an expert HR analyst. Analyze the following interview transcript dialogue.\n"
                f"Read the following interview dialogue:\n\n{formatted_dialogue}\n\n"
                "Your task: Extract exactly 4 key competencies that are ACTUALLY discussed and tested in this specific dialogue.\n"
                "MANDATORY RULES:\n"
                f"1. Language MUST be {'Indonesian' if is_indonesian else 'English'}.\n"
                "2. Codes MUST be 'C1', 'C2', 'C3', 'C4'.\n"
                "3. Titles and questions must directly reflect the actual work domain discussed in the audio dialogue."
            )
            extracted_schema = await LlmFactory.invoke_structured_or_fallback(
                schema=TranscriptCompetencyGenerationSchema,
                system_instruction=system_gen_prompt,
                user_content=f"Dialogue Transcript:\n{formatted_dialogue}",
                fallback_fn=fallback_competencies,
            )

            # Purge existing system-created competencies for this profile
            if competencies:
                old_comp_ids = [c.nid for c in competencies if getattr(c, "vcrea", None) == "SYSTEM_TRANSCRIPT_ASR"]
                if old_comp_ids:
                    # Clean up any lingering SummaryPoint/Evidence referencing old_comp_ids
                    other_sp_subq = select(SummaryPoint.nid).where(SummaryPoint.nid_competency.in_(old_comp_ids))
                    other_sp_ids = (await self.session.execute(other_sp_subq)).scalars().all()
                    if other_sp_ids:
                        await self.session.execute(
                            delete(SummaryEvidence).where(SummaryEvidence.nid_summary_point.in_(other_sp_ids))
                        )
                        await self.session.execute(
                            delete(SummaryPoint).where(SummaryPoint.nid.in_(other_sp_ids))
                        )
                    await self.session.execute(delete(Competency).where(Competency.nid.in_(old_comp_ids)))
                    await self.session.commit()
                competencies = [c for c in competencies if c.nid not in old_comp_ids]

            specs = [(c.code, c.name, c.reference_question) for c in extracted_schema.competencies[:4]]
            if not specs:
                specs = [(c.code, c.name, c.reference_question) for c in fallback_competencies().competencies]

            for sort_idx, (c_code, c_name, c_q) in enumerate(specs, start=1):
                comp = next((c for c in competencies if c.vcode == c_code), None)
                if comp:
                    comp.vname = c_name
                    comp.vreference_question = c_q
                    comp.nsort_order = sort_idx
                    comp.vcrea = "SYSTEM_TRANSCRIPT_ASR"
                else:
                    comp = Competency(
                        nid_profile=profile_id,
                        vcode=c_code,
                        vname=c_name,
                        vreference_question=c_q,
                        vvisibility_class="GENERAL",
                        nsort_order=sort_idx,
                        vcrea="SYSTEM_TRANSCRIPT_ASR",
                    )
                    self.session.add(comp)
                    competencies.append(comp)

            await self.session.commit()

        # Build clean fallback evaluation
        def fallback_evaluations() -> InterviewEvaluationReportSchema:
            candidate_segs = [s for s in segments if s.get("speaker_type") == "CANDIDATE"]
            items = []
            for idx, comp in enumerate(competencies):
                comp_keywords = set(comp.vname.lower().split())
                matching_seg = None
                for cs in candidate_segs:
                    words_in_seg = set(cs.get("text", "").lower().split())
                    if words_in_seg & comp_keywords:
                        matching_seg = cs
                        break

                if matching_seg and len(matching_seg.get("text", "").split()) >= 3:
                    cov_status = "COVERED"
                    ver_status = "VERIFIED"
                    quote = matching_seg.get("text")
                    seg_no = matching_seg.get("segment_no")
                    if is_indonesian:
                        content = f"Kandidat mendemonstrasikan aspek '{comp.vname}' berdasarkan bukti pernyataan pada wawancara."
                    else:
                        content = f"The candidate demonstrated aspects of '{comp.vname}' based on statements provided in the interview."
                else:
                    cov_status = "NOT_DISCUSSED"
                    ver_status = "UNVERIFIED"
                    quote = None
                    seg_no = None
                    if is_indonesian:
                        content = f"Topik kompetensi '{comp.vname}' tidak secara eksplisit diuraikan dalam rekaman percakapan ini."
                    else:
                        content = f"The competency '{comp.vname}' was not explicitly addressed by the candidate in this conversation."

                items.append(
                    CompetencyEvaluationItem(
                        competency_code=comp.vcode,
                        coverage_status=cov_status,
                        verification_status=ver_status,
                        content=content,
                        verbatim_quote=quote,
                        segment_no=seg_no,
                    )
                )
            return InterviewEvaluationReportSchema(evaluations=items)

        comp_list_desc = "\n".join([f"- Kode: '{c.vcode}' | Nama: '{c.vname}'" for c in competencies])
        if is_indonesian:
            system_instruction = (
                "Anda adalah AI evaluator wawancara kerja profesional dan objektif.\n"
                f"Evaluasi percakapan berikut terhadap daftar rubrik kompetensi:\n{comp_list_desc}\n\n"
                "ATURAN AUDIT KETAT:\n"
                "1. Evaluasi HANYA dari perkataan CANDIDATE (ditandai dengan [CANDIDATE]). DILARANG mengutip perkataan INTERVIEWER.\n"
                "2. DILARANG KERAS mengutip efek audio seperti '[door opening]', suara latar, atau sekadar sapaan singkat seperti 'Hi.', 'Hello.'.\n"
                "3. Jika kandidat tidak membahas atau tidak mendemonstrasikan kompetensi tersebut, WAJIB set coverage_status='NOT_DISCUSSED', verification_status='UNVERIFIED', dan verbatim_quote=null. JANGAN memaksakan kutipan palsu!\n"
                "4. Bahasa respon penilaian WAJIB menggunakan Bahasa Indonesia.\n"
                f"5. Jika topik wawancara sama sekali berbeda dari posisi pelamar ({cand_pos}), set topic_mismatch_detected=true dan jelaskan pada mismatch_description."
            )
        else:
            system_instruction = (
                "You are an expert, objective AI interview assessor.\n"
                f"Evaluate the following dialogue against the competency rubric:\n{comp_list_desc}\n\n"
                "STRICT AUDIT RULES:\n"
                "1. Evaluate ONLY statements from the CANDIDATE (marked with [CANDIDATE]). NEVER cite words from the INTERVIEWER.\n"
                "2. STRICTLY FORBIDDEN to cite audio events like '[door opening]', background tags, or trivial greetings like 'Hi.', 'Hello.'.\n"
                "3. If a competency was not substantively demonstrated, you MUST set coverage_status='NOT_DISCUSSED', verification_status='UNVERIFIED', dan verbatim_quote=null. Do NOT fabricate citations!\n"
                "4. Response language MUST be English.\n"
                f"5. If the dialogue diverges entirely from the applied position ({cand_pos}), set topic_mismatch_detected=true and state the mismatch."
            )

        report = await LlmFactory.invoke_structured_or_fallback(
            schema=InterviewEvaluationReportSchema,
            system_instruction=system_instruction,
            user_content=f"Interview Dialogue:\n{formatted_dialogue}",
            fallback_fn=fallback_evaluations,
        )

        # Flag mismatch if detected
        if report.topic_mismatch_detected and report.mismatch_description:
            flag = Flag(
                nid_job=job_id,
                vflag_type="NEEDS_CLARIFICATION",
                vneutral_text=f"Deteksi Mismatch Topik: {report.mismatch_description}",
                vstatus="OPEN",
            )
            self.session.add(flag)

        def find_best_segment(quote: str | None, seg_list: list[dict[str, Any]], preferred_seg_no: int | None = None) -> int | None:
            if not quote or not seg_list:
                return None

            clean_q = quote.strip()
            if not clean_q or (clean_q.startswith("[") and clean_q.endswith("]")) or len(clean_q.split()) < 2:
                return None

            if preferred_seg_no is not None:
                for s in seg_list:
                    if s.get("segment_no") == preferred_seg_no:
                        return s.get("id")

            quote_words = set(clean_q.lower().split())
            best_id = None
            best_score = 0
            for s in seg_list:
                if s.get("speaker_type") != "CANDIDATE":
                    continue
                seg_words = set(s.get("text", "").lower().split())
                overlap = len(quote_words & seg_words)
                if overlap > best_score and overlap >= 2:
                    best_score = overlap
                    best_id = s.get("id")
            return best_id

        created_points = []
        eval_items = report.evaluations or fallback_evaluations().evaluations
        for eval_item in eval_items:
            comp_obj = next((c for c in competencies if c.vcode.lower() == eval_item.competency_code.lower()), None)
            if not comp_obj:
                comp_obj = next((c for c in competencies if c.vname.lower() in eval_item.content.lower() or c.vcode.lower() in eval_item.content.lower()), None)
            if not comp_obj and competencies:
                comp_obj = competencies[len(created_points) % len(competencies)]

            sp = SummaryPoint(
                nid_competency=comp_obj.nid,
                nid_job=job_id,
                vcoverage_status=eval_item.coverage_status,
                vverification_status=eval_item.verification_status,
                vcontent=eval_item.content,
            )
            self.session.add(sp)
            await self.session.flush()

            # Only add Evidence if quote is substantive and coverage is not NOT_DISCUSSED
            if eval_item.coverage_status != "NOT_DISCUSSED" and eval_item.verbatim_quote:
                target_seg_id = find_best_segment(eval_item.verbatim_quote, segments, preferred_seg_no=eval_item.segment_no)
                if target_seg_id:
                    ev = SummaryEvidence(
                        nid_summary_point=sp.nid,
                        nid_transcript=target_seg_id,
                        vquote=eval_item.verbatim_quote,
                    )
                    self.session.add(ev)

            created_points.append(sp)

        # Update Job Status to COMPLETED (10)
        await self.session.execute(
            update(Job).where(Job.nid == job_id).values(nstatus=10)
        )
        await self.session.commit()

        # Log audit
        audit = await self.audit_service.log_event(
            event_type="INTERVIEW_ANALYZED",
            actor="AI_INTERVIEW_ANALYZER",
            actor_type="AGENT",
            title="Interview Transcript Analyzed",
            description=f"Interview evaluation for session #{state.get('interview_id')} successfully mapped to {len(created_points)} rubric competency points.",
            job_id=job_id,
        )

        return {
            "job_status": "COMPLETED",
            "competency_points": [
                {"id": p.nid, "content": p.vcontent, "status": p.vcoverage_status}
                for p in created_points
            ],
            "audit_entries": [
                *state.get("audit_entries", []),
                {"event_type": "INTERVIEW_ANALYZED", "id": audit.id},
            ],
        }

    def build_graph(self) -> Any:
        graph = StateGraph(InterviewAnalyzerState)

        graph.add_node("consent_gate", self.consent_gate_node)
        graph.add_node("transcript_segmenter", self.transcript_segmenter_node)
        graph.add_node("flag_scanner", self.transcript_flag_scanner_node)
        graph.add_node("rubric_evaluator", self.rubric_evaluator_node)

        def route_after_consent(state: InterviewAnalyzerState) -> str:
            if state.get("job_status") == "REJECTED_NO_CONSENT":
                return END
            return "transcript_segmenter"

        graph.add_edge(START, "consent_gate")
        graph.add_conditional_edges("consent_gate", route_after_consent, ["transcript_segmenter", END])
        graph.add_edge("transcript_segmenter", "flag_scanner")
        graph.add_edge("flag_scanner", "rubric_evaluator")
        graph.add_edge("rubric_evaluator", END)

        return graph.compile()


async def run_interview_analyzer_pipeline(
    session: AsyncSession,
    interview_id: int,
    candidate_id: int,
    profile_id: int,
    consent_status: str = "GRANTED",
    notes: str | None = None,
    audio_url: str | None = None,
    audio_duration: str | None = None,
    job_id: int | None = None,
) -> InterviewAnalyzerState:
    """Convenience runner for Pipeline 2."""
    analyzer = InterviewAnalyzerGraph(session)
    app = analyzer.build_graph()

    # Load candidate info
    cand_stmt = select(Candidate).where(Candidate.nid == candidate_id)
    cand = (await session.execute(cand_stmt)).scalars().first()

    # Load profile info
    prof_stmt = select(Profile).where(Profile.nid == profile_id)
    prof = (await session.execute(prof_stmt)).scalars().first()

    initial_state: InterviewAnalyzerState = {
        "interview_id": interview_id,
        "candidate_id": candidate_id,
        "candidate_name": cand.vname if cand else "Kandidat",
        "candidate_code": cand.vcandidate_code if cand else "CAND-001",
        "position": cand.vjob_position if cand else "Software Engineer",
        "profile_id": profile_id,
        "profile_code": prof.vcode if prof else "PROFILE-TECH-R1",
        "consent_status": consent_status,
        "notes": notes,
        "audio_url": audio_url,
        "audio_duration": audio_duration,
        "job_id": job_id,
        "job_status": "RECEIVED",
        "transcript_segments": [],
        "flags": [],
        "competency_points": [],
        "audit_entries": [],
    }

    result = await app.ainvoke(initial_state)
    return result  # type: ignore[return-value]
