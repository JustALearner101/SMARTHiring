"use client";

import { Link, usePathname } from "@/i18n/navigation";
import { cn } from "@/utils";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSidebar } from "../context/SidebarContext";
import {
  BoltIcon,
  ChatIcon,
  ChevronDownIcon,
  DocsIcon,
  FolderIcon,
  GridIcon,
  HorizontaLDots,
  PageIcon,
} from "../icons/index";

import type { UserRole } from "@/types/auth";

type NavItem = {
  key: string;
  icon: React.ReactNode;
  path?: string;
  roles?: UserRole[];
  new?: boolean;
  target?: string;
  subItems?: {
    key: string;
    path: string;
    roles?: UserRole[];
    pro?: boolean;
    new?: boolean;
    target?: string;
  }[];
};

const navItems: NavItem[] = [
  {
    icon: <GridIcon />,
    key: "dashboard",
    path: "/",
    roles: ["HR", "ADMIN", "INTERVIEWER"],
  },
  {
    icon: <BoltIcon />,
    key: "orchestration",
    roles: ["HR", "ADMIN", "INTERVIEWER"],
    subItems: [
      { key: "scheduling", path: "/orchestration/scheduling", roles: ["HR", "ADMIN"] },
      { key: "triageThreads", path: "/orchestration/threads", roles: ["HR", "ADMIN"] },
      { key: "calendarMatrix", path: "/orchestration/calendar", roles: ["HR", "ADMIN", "INTERVIEWER"] },
    ],
  },
  {
    icon: <PageIcon />,
    key: "interviews",
    roles: ["HR", "ADMIN", "INTERVIEWER"],
    subItems: [
      { key: "interviewSessions", path: "/interviews/sessions", roles: ["HR", "ADMIN", "INTERVIEWER"] },
      { key: "reviewEvidence", path: "/interviews/review", roles: ["HR", "ADMIN", "INTERVIEWER"] },
    ],
  },
  {
    icon: <FolderIcon />,
    key: "masterData",
    roles: ["HR", "ADMIN", "INTERVIEWER"],
    subItems: [
      { key: "candidates", path: "/master/candidates", roles: ["HR", "ADMIN"] },
      { key: "contacts", path: "/master/contacts", roles: ["HR", "ADMIN"] },
      { key: "rubrics", path: "/master/rubrics", roles: ["HR", "ADMIN", "INTERVIEWER"] },
      { key: "operationalRules", path: "/master/operational-rules", roles: ["HR", "ADMIN"] },
    ],
  },
  {
    icon: <ChatIcon />,
    key: "simulator",
    roles: ["HR", "ADMIN", "INTERVIEWER"],
    subItems: [
      { key: "interviewerEmail", path: "/simulator/email", roles: ["HR", "ADMIN", "INTERVIEWER"] },
      { key: "candidateWhatsapp", path: "/simulator/whatsapp", roles: ["HR", "ADMIN"] },
    ],
  },
  {
    icon: <DocsIcon />,
    key: "auditSecurity",
    roles: ["ADMIN"],
    subItems: [
      { key: "auditLogs", path: "/audit/logs", roles: ["ADMIN"] },
      { key: "guardrailAlerts", path: "/audit/guardrail", roles: ["ADMIN"] },
    ],
  },
];

const AppSidebar: React.FC = () => {
  const { isExpanded, isMobileOpen, isHovered, setIsHovered } = useSidebar();
  const { role } = useAuth();
  const pathname = usePathname();
  const t = useTranslations("sidebar");

  const filteredNavItems = useMemo(() => {
    if (!role) return navItems;

    return navItems
      .filter((item) => !item.roles || item.roles.includes(role))
      .map((item) => {
        if (!item.subItems) return item;
        const validSubs = item.subItems.filter(
          (sub) => !sub.roles || sub.roles.includes(role)
        );
        return { ...item, subItems: validSubs };
      })
      .filter((item) => !item.subItems || item.subItems.length > 0);
  }, [role]);

  const renderMenuItems = (
    navItems: NavItem[],
    menuType: "main" | "support" | "others",
  ) => (
    <ul className="flex flex-col gap-1">
      {navItems.map((nav, index) => (
        <li key={nav.key}>
          {nav.subItems ? (
            <button
              onClick={() => handleSubmenuToggle(index, menuType)}
              className={cn(
                "group menu-item cursor-pointer",
                openSubmenu?.type === menuType && openSubmenu?.index === index
                  ? "menu-item-active"
                  : "menu-item-inactive",
                !isExpanded && !isHovered
                  ? "lg:justify-center"
                  : "lg:justify-start",
              )}
            >
              <span
                className={cn(
                  openSubmenu?.type === menuType && openSubmenu?.index === index
                    ? "menu-item-icon-active"
                    : "menu-item-icon-inactive",
                )}
              >
                {nav.icon}
              </span>
              {(isExpanded || isHovered || isMobileOpen) && (
                <>
                  <span className="menu-item-text truncate">{t(`items.${nav.key}`)}</span>
                  <div className="ms-auto flex items-center gap-1.5 shrink-0">
                    {nav.new && (
                      <span
                        className={cn(
                          openSubmenu?.type === menuType &&
                            openSubmenu?.index === index
                            ? "menu-dropdown-badge-active"
                            : "menu-dropdown-badge-inactive",
                          "menu-dropdown-badge text-[10px] px-1.5 py-0.5",
                        )}
                      >
                        {t("badges.new")}
                      </span>
                    )}
                    <ChevronDownIcon
                      className={cn(
                        "h-5 w-5 transition-transform duration-200",
                        openSubmenu?.type === menuType &&
                          openSubmenu?.index === index
                          ? "rotate-180 text-brand-500"
                          : "",
                      )}
                    />
                  </div>
                </>
              )}
            </button>
          ) : (
            nav.path && (
              <Link
                href={nav.path}
                target={nav.target}
                className={cn(
                  "group menu-item",
                  isActive(nav.path)
                    ? "menu-item-active"
                    : "menu-item-inactive",
                )}
              >
                <span
                  className={cn(
                    isActive(nav.path)
                      ? "menu-item-icon-active"
                      : "menu-item-icon-inactive",
                  )}
                >
                  {nav.icon}
                </span>
                {(isExpanded || isHovered || isMobileOpen) && (
                  <span className="menu-item-text">
                    {t(`items.${nav.key}`)}
                  </span>
                )}
              </Link>
            )
          )}
          {nav.subItems && (isExpanded || isHovered || isMobileOpen) && (
            <div
              ref={(el) => {
                subMenuRefs.current[`${menuType}-${index}`] = el;
              }}
              className="overflow-hidden transition-all duration-300"
              style={{
                height:
                  openSubmenu?.type === menuType && openSubmenu?.index === index
                    ? `${subMenuHeight[`${menuType}-${index}`]}px`
                    : "0px",
              }}
            >
              <ul className="ms-9 mt-2 space-y-1">
                {nav.subItems.map((subItem) => (
                  <li key={subItem.key}>
                    <Link
                      href={subItem.path}
                      target={subItem.target}
                      className={`menu-dropdown-item ${
                        isActive(subItem.path)
                          ? "menu-dropdown-item-active"
                          : "menu-dropdown-item-inactive"
                      }`}
                    >
                      {t(`items.${subItem.key}`)}
                      <span className="ms-auto flex items-center gap-1">
                        {subItem.new && (
                          <span
                            className={`ms-auto ${
                              isActive(subItem.path)
                                ? "menu-dropdown-badge-active"
                                : "menu-dropdown-badge-inactive"
                            } menu-dropdown-badge`}
                          >
                            {t("badges.new")}
                          </span>
                        )}
                        {subItem.pro && (
                          <span
                            className={`ms-auto ${
                              isActive(subItem.path)
                                ? "menu-dropdown-badge-pro-active"
                                : "menu-dropdown-badge-pro-inactive"
                            } menu-dropdown-badge-pro`}
                          >
                            {t("badges.pro")}
                          </span>
                        )}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </li>
      ))}
    </ul>
  );

  const [openSubmenu, setOpenSubmenu] = useState<{
    type: "main" | "support" | "others";
    index: number;
  } | null>(null);
  const [subMenuHeight, setSubMenuHeight] = useState<Record<string, number>>(
    {},
  );
  const subMenuRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // const isActive = (path: string) => path === pathname;

  const isActive = useCallback((path: string) => path === pathname, [pathname]);

  useEffect(() => {
    // Check if the current path matches any submenu item
    let submenuMatched = false;
    filteredNavItems.forEach((nav, index) => {
      if (nav.subItems) {
        nav.subItems.forEach((subItem) => {
          if (isActive(subItem.path)) {
            setOpenSubmenu({
              type: "main",
              index,
            });
            submenuMatched = true;
          }
        });
      }
    });

    // If no submenu item matches, close the open submenu
    if (!submenuMatched) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- collapse submenu when the route no longer matches
      setOpenSubmenu(null);
    }
  }, [pathname, isActive, filteredNavItems]);

  useEffect(() => {
    // Set the height of the submenu items when the submenu is opened
    if (openSubmenu !== null) {
      const key = `${openSubmenu.type}-${openSubmenu.index}`;
      if (subMenuRefs.current[key]) {
        setSubMenuHeight((prevHeights) => ({
          ...prevHeights,
          [key]: subMenuRefs.current[key]?.scrollHeight || 0,
        }));
      }
    }
  }, [openSubmenu]);

  const handleSubmenuToggle = (
    index: number,
    menuType: "main" | "support" | "others",
  ) => {
    setOpenSubmenu((prevOpenSubmenu) => {
      if (
        prevOpenSubmenu &&
        prevOpenSubmenu.type === menuType &&
        prevOpenSubmenu.index === index
      ) {
        return null;
      }
      return { type: menuType, index };
    });
  };

  return (
    <aside
      className={`fixed top-0 left-0 z-50 flex h-full flex-col border-r border-gray-200 bg-white px-5 text-gray-900 transition-all duration-300 ease-in-out xl:mt-0 rtl:right-0 rtl:left-auto rtl:border-r-0 rtl:border-l dark:border-gray-800 dark:bg-gray-900 ${
        isExpanded || isMobileOpen ? "w-72.5" : isHovered ? "w-72.5" : "w-22.5"
      } ${
        isMobileOpen
          ? "translate-x-0"
          : "-translate-x-full rtl:translate-x-full"
      } xl:translate-x-0 xl:rtl:translate-x-0`}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={`flex py-8 ${
          !isExpanded && !isHovered ? "xl:justify-center" : "justify-start"
        }`}
      >
        <Link href="/" className="flex items-center gap-3">
          {/* <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-white font-bold text-lg shadow-theme-xs">
            <BoltIcon className="w-6.5 h-6.5 text-white" />
          </div> */}
          {(isExpanded || isHovered || isMobileOpen) && (
            <div className="flex flex-col">
              <span className="text-base font-bold text-gray-900 dark:text-white leading-tight">
                SmartHiring
              </span>
              <span className="text-[10px] font-medium text-brand-500 uppercase tracking-wider">
                AI Orchestrator
              </span>
            </div>
          )}
        </Link>
      </div>
      <div className="no-scrollbar flex flex-col overflow-y-auto duration-300 ease-linear">
        <nav className="mb-6">
          <div className="flex flex-col gap-4">
            <div>
              <h2
                className={`mb-4 flex text-xs leading-5 text-gray-400 uppercase ${
                  !isExpanded && !isHovered
                    ? "xl:justify-center"
                    : "justify-start"
                }`}
              >
                {isExpanded || isHovered || isMobileOpen ? (
                  t("groups.menu")
                ) : (
                  <HorizontaLDots />
                )}
              </h2>
              {renderMenuItems(filteredNavItems, "main")}
            </div>
          </div>
        </nav>
      </div>
    </aside>
  );
};

export default AppSidebar;
