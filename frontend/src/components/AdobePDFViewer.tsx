// src/components/AdobePDFViewer.tsx
import React, { useEffect, useRef, useState } from 'react';
import type { AdobeDCView } from '@/types/adobe';

interface AdobePDFViewerProps {
  file: File | null;
  onTextSelection: (text: string) => void;
  targetPage: number | null;
}

const ADOBE_VIEWER_ID = 'adobe-dc-view';
const ADOBE_SDK_URL = 'https://acrobatservices.adobe.com/view-sdk/viewer.js';

const AdobePDFViewer = ({ file, onTextSelection, targetPage }: AdobePDFViewerProps) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const adobeDCViewRef = useRef<AdobeDCView | null>(null);
  const apisRef = useRef<any>(null);
  const [sdkReady, setSdkReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Effect to load the Adobe SDK script
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
    script.onerror = () => setError('Failed to load Adobe SDK.');
    document.head.appendChild(script);
    return () => { 
      if (document.head.contains(script)) {
        document.head.removeChild(script); 
      }
    };
  }, []);

  // Effect to initialize the viewer and load the PDF file
  useEffect(() => {
    if (!sdkReady || !file) return;

    let isComponentMounted = true;
    
    const initializeAndPreview = async () => {
      console.log('Attempting to initialize viewer...');
      try {
        const clientId = import.meta.env.VITE_ADOBE_CLIENT_ID;
        if (!clientId) throw new Error('VITE_ADOBE_CLIENT_ID is not configured.');

        // Create the viewer instance
        adobeDCViewRef.current = new window.AdobeDC.View({
          clientId,
          divId: ADOBE_VIEWER_ID,
        });

        // Event options structure
        const eventOptions = {
          listenOn: [window.AdobeDC.View.Enum.FilePreviewEvents.PREVIEW_SELECTION_END],
          enableFilePreviewEvents: true
        };

        // Register callback BEFORE previewFile
        adobeDCViewRef.current.registerCallback(
          window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
          async (event: any) => {
            if (event.type === window.AdobeDC.View.Enum.FilePreviewEvents.PREVIEW_SELECTION_END) {
              console.log('✅ PREVIEW_SELECTION_END event fired!');
              
              if (apisRef.current) {
                setTimeout(async () => {
                  try {
                    const result = await apisRef.current.getSelectedContent();
                    const selectedText = result.data?.trim();
                    
                    if (selectedText && selectedText.length > 0) {
                      console.log('Selected text:', selectedText);
                      onTextSelection(selectedText);
                    }
                  } catch (e) {
                    console.error("❌ Could not get selected content:", e);
                  }
                }, 50);
              }
            }
          },
          eventOptions
        );

        // Get file content and preview
        const arrayBuffer = await file.arrayBuffer();
        const previewFilePromise = adobeDCViewRef.current.previewFile(
          {
            content: { promise: Promise.resolve(arrayBuffer) },
            metaData: { fileName: file.name },
          },
          { 
            embedMode: 'SIZED_CONTAINER', 
            defaultViewMode: 'FIT_WIDTH'
          }
        );

        // Store APIs reference when preview is ready
        previewFilePromise.then(async (adobeViewer) => {
          if (!isComponentMounted || !adobeDCViewRef.current) return;

          console.log('✅ PDF Preview is ready. Getting APIs...');
          try {
            apisRef.current = await adobeViewer.getAPIs();
            console.log('✅ APIs stored successfully');

            // ✅ NAVIGATE HERE: After APIs are ready and targetPage exists
            if (targetPage && targetPage > 0) {
              console.log(`🔄 Attempting to navigate to page ${targetPage}...`);
              
              // Add small delay to ensure PDF is fully rendered
              setTimeout(() => {
                if (apisRef.current && typeof apisRef.current.gotoLocation === 'function') {
                  apisRef.current.gotoLocation(targetPage) // ✅ CORRECT: Direct number parameter
                    .then(() => {
                      console.log(`✅ Successfully navigated to page ${targetPage}`);
                    })
                    .catch((error: any) => {
                      console.error(`❌ Navigation failed:`, error);
                    });
                } else {
                  console.error('❌ gotoLocation method not available');
                }
              }, 100); // Small delay for PDF rendering
            }
          } catch (e) {
            console.error("❌ Could not get APIs:", e);
          }
        });

      } catch (err: any) {
        if (isComponentMounted) setError(err.message);
      }
    };

    initializeAndPreview();
    
    return () => { 
      isComponentMounted = false;
      apisRef.current = null;
    };
  }, [sdkReady, file, onTextSelection, targetPage]); // ✅ ADDED targetPage to dependencies

  if (error) {
    return (
      <div className="p-4 text-red-600 flex items-center justify-center h-full">
        {error}
      </div>
    );
  }

  return (
    <div id={ADOBE_VIEWER_ID} ref={viewerRef} className="w-full h-full">
      {!file && (
        <div className="p-4 flex items-center justify-center h-full">
          Please upload a PDF to begin.
        </div>
      )}
    </div>
  );
};

export default AdobePDFViewer;
