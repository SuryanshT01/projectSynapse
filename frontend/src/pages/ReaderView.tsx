import { useState } from 'react';
import LibrarySidebar from '@/components/LibrarySidebar';
import PDFViewer from '@/components/PDFViewer';
import RightSidebar from '@/components/RightSidebar';
import TextSelectionSidebar from '@/components/TextSelectionSidebar';

const ReaderView = () => {
  const [selectedPDF, setSelectedPDF] = useState<string>();
  const [isTextSidebarOpen, setIsTextSidebarOpen] = useState(false);
  const [selectedText, setSelectedText] = useState('');

  const handlePDFSelect = (pdfId: string) => {
    setSelectedPDF(pdfId);
  };

  const handleSectionSelect = (sectionId: string) => {
    console.log('Navigating to section:', sectionId);
    // TODO: Send to backend to scroll/navigate PDF viewer to specific section
  };

  const handleTextSelection = (text: string) => {
    setSelectedText(text);
    setIsTextSidebarOpen(true);
  };

  const handlePromptSubmit = (prompt: string, selectedText: string) => {
    console.log('Prompt submitted:', prompt);
    console.log('Selected text:', selectedText);
    // TODO: Send to backend for processing
  };

  return (
    <div className="h-screen bg-background flex">
      {/* Left Sidebar - PDF Sections */}
      <LibrarySidebar selectedPDF={selectedPDF} onSectionSelect={handleSectionSelect} />
      
      {/* Center Panel - PDF Viewer */}
      <div className="flex-1 p-4">
        <PDFViewer selectedPDF={selectedPDF} onTextSelection={handleTextSelection} />
      </div>
      
      {/* Right Sidebar */}
      <RightSidebar onPDFSelect={handlePDFSelect} />

      {/* Text Selection Sidebar */}
      <TextSelectionSidebar
        isOpen={isTextSidebarOpen}
        selectedText={selectedText}
        onClose={() => setIsTextSidebarOpen(false)}
        onPromptSubmit={handlePromptSubmit}
      />
    </div>
  );
};

export default ReaderView;