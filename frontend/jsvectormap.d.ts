declare module "jsvectormap" {
  export default class jsVectorMap {
    constructor(options: Record<string, unknown>);
    destroy(): void;
    updateSize(): void;
  }
}
