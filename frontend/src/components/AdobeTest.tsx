import { useEffect, useRef } from 'react';

const AdobeTest = () => {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simple Adobe test
    const testAdobe = async () => {
      console.log('Testing Adobe API...');
      
      // Check if Adobe is available
      if (window.AdobeDC) {
        console.log('✅ Adobe API is available');
        
        if (viewerRef.current) {
          console.log('✅ Viewer div is ready');
          
          try {
            const clientId = import.meta.env.VITE_ADOBE_CLIENT_ID;
            console.log('Client ID:', clientId);
            
            if (clientId && clientId !== 'your-adobe-client-id-here') {
              const viewer = new window.AdobeDC.View({
                clientId: clientId,
                divId: viewerRef.current.id
              });
              
              console.log('✅ Adobe viewer created successfully');
              
              // Test with a simple PDF
              const testPdfUrl = 'https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf';
              
              viewer.previewFile({
                content: { location: { url: testPdfUrl } },
                metaData: { fileName: 'Test PDF' }
              }, {
                defaultViewMode: 'FIT_WIDTH',
                showDownloadPDF: false,
                showPrintPDF: false
              });
              
              console.log('✅ Test PDF loaded');
            } else {
              console.error('❌ Client ID not configured');
            }
          } catch (error) {
            console.error('❌ Adobe viewer creation failed:', error);
          }
        } else {
          console.error('❌ Viewer div not ready');
        }
      } else {
        console.error('❌ Adobe API not available');
      }
    };

    // Load Adobe script if not available
    if (!window.AdobeDC) {
      const script = document.createElement('script');
      script.src = 'https://acrobatservices.adobe.com/view-sdk/viewer.js';
      script.async = true;
      
      script.onload = () => {
        console.log('Adobe script loaded, testing...');
        setTimeout(testAdobe, 100);
      };
      
      script.onerror = () => {
        console.error('Failed to load Adobe script');
      };
      
      document.head.appendChild(script);
    } else {
      testAdobe();
    }
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Adobe PDF API Test</h2>
      <div 
        ref={viewerRef}
        id="adobe-test-viewer"
        className="w-full h-96 border border-gray-300 rounded"
      />
      <div className="mt-4 text-sm text-gray-600">
        Check browser console for test results
      </div>
    </div>
  );
};

export default AdobeTest;
