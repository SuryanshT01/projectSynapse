// src/types/adobe.d.ts
declare global {
  interface Window {
    AdobeDC?: {
      View: {
        new (config: AdobeViewConfig): AdobeDCView;
        Enum: {
          CallbackType: { 
            EVENT_LISTENER: any;
          };
          FilePreviewEvents: {
            PREVIEW_SELECTION_END: any;
            // ... other events
          };
        };
      };
    };
  }
}

export interface AdobeViewConfig {
  clientId: string;
  divId: string;
}

export interface AdobeDCView {
  previewFile(
    fileConfig: {
      content: { promise: Promise<ArrayBuffer | Uint8Array> };
      metaData: { fileName: string };
    },
    viewerConfig?: AdobeViewerConfig
  ): Promise<AdobeViewer>;

  registerCallback(
    type: any,
    callback: (event: any) => void,
    options?: any
  ): void;
}

export interface AdobeViewer {
  getAPIs(): Promise<AdobeAPIs>;
}

export interface AdobeAPIs {
  getSelectedContent(): Promise<{ type: 'text'; data: string }>;
}

export interface AdobeViewerConfig {
  embedMode?: 'SIZED_CONTAINER' | 'FULL_WINDOW' | 'IN_LINE' | 'LIGHTBOX';
  defaultViewMode?: 'FIT_WIDTH' | 'FIT_PAGE' | 'TWO_COLUMN' | 'TWO_COLUMN_FIT_PAGE';
}

export {};
