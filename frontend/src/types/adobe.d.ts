// src/types/adobe.d.ts
declare global {
    interface Window {
      AdobeDC?: {
        View: {
          // The constructor is part of the View class
          new (config: AdobeViewConfig): AdobeDCView;
          // The Enum object is also a static property of the View class
          Enum: {
            CallbackType: { EVENT_LISTENER: any };
            Events: { PREVIEW_SELECTION_END: any };
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
    embedMode?: 'SIZED_CONTAINER';
    defaultViewMode?: 'FIT_WIDTH';
  }
  
  export {};