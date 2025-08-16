// src/components/AdobePDFViewer.tsx
import React, { useEffect, useRef, useState } from 'react';
import type { AdobeDCView } from '@/types/adobe';

interface AdobePDFViewerProps {
  file: File | null;
  onTextSelection: (text: string) => void;
}

const ADOBE_VIEWER_ID = 'adobe-dc-view';
const ADOBE_SDK_URL = 'https://acrobatservices.adobe.com/view-sdk/viewer.js';

const AdobePDFViewer = ({ file, onTextSelection }: AdobePDFViewerProps) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const [sdkReady, setSdkReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Load the Adobe SDK Script once.
  useEffect(() => {
    if (window.AdobeDC) {
      setSdkReady(true);
      return;
    }

    const script = document.createElement('script');
    script.src = ADOBE_SDK_URL;
    script.async = true;
    script.onload = () => {
      document.addEventListener('adobe_dc_view_sdk.ready', () => {
        setSdkReady(true);
      });
    };
    script.onerror = () => {
      setError('Failed to load the Adobe SDK script. Check adblockers or network issues.');
    };
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  // Step 2: Initialize the viewer when the SDK is ready and a file is provided.
  useEffect(() => {
    if (!sdkReady || !file || !viewerRef.current) {
      return;
    }
    
    let isComponentMounted = true;
    viewerRef.current.innerHTML = '';

    const initialize = async () => {
      try {
        const clientId = import.meta.env.VITE_ADOBE_CLIENT_ID;
        if (!clientId) throw new Error('VITE_ADOBE_CLIENT_ID is not configured.');

        // This line is correct
        const adobeDCView: AdobeDCView = new window.AdobeDC.View({
          clientId,
          divId: ADOBE_VIEWER_ID,
        });

        const arrayBuffer = await file.arrayBuffer();

        const previewFilePromise = adobeDCView.previewFile(
          {
            content: { promise: Promise.resolve(arrayBuffer) },
            metaData: { fileName: file.name },
          },
          { embedMode: 'SIZED_CONTAINER', defaultViewMode: 'FIT_WIDTH' }
        );

        previewFilePromise.then((adobeViewer) => {
          if (!isComponentMounted || !window.AdobeDC) return;

          // ✅ FIX: Changed AdobeDC.Enum to AdobeDC.View.Enum
          adobeDCView.registerCallback(
            window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
            async (event: any) => {
              // ✅ FIX: Changed AdobeDC.Enum to AdobeDC.View.Enum
              if (event.type === window.AdobeDC.View.Enum.Events.PREVIEW_SELECTION_END) {
                console.log('✅ PREVIEW_SELECTION_END event fired! Getting content...');
                try {
                  const apis = await adobeViewer.getAPIs();
                  const result = await apis.getSelectedContent();
                  const selectedText = result.data.trim();
                  
                  if (selectedText) {
                    console.log(`✅ Text selected: "${selectedText}"`);
                    onTextSelection(selectedText);
                  }
                } catch (e) {
                  console.error("❌ Could not get selected content:", e);
                }
              }
            },
            {
              enableFilePreviewEvents: true,
              // ✅ FIX: Changed AdobeDC.Enum to AdobeDC.View.Enum
              listenOn: [window.AdobeDC.View.Enum.Events.PREVIEW_SELECTION_END],
            }
          );
        });

      } catch (err: any) {
        if (isComponentMounted) {
          setError(err.message);
        }
      }
    };
    initialize();
    return () => {
      isComponentMounted = false;
    };
  }, [sdkReady, file, onTextSelection]);

  if (error) {
    return <div className="p-4 text-red-600 flex items-center justify-center h-full">{error}</div>;
  }

  return (
    <div id={ADOBE_VIEWER_ID} ref={viewerRef} className="w-full h-full">
      {!sdkReady && <div className="p-4 flex items-center justify-center h-full">Loading Adobe Viewer...</div>}
    </div>
  );
};

export default AdobePDFViewer;