// src/components/PDFViewer.tsx
import AdobePDFViewer from './AdobePDFViewer';

interface PDFViewerProps {
  onTextSelection: (text: string) => void;
  uploadedFile: File | null;
  targetPage?: number | null;
}

const PDFViewer = ({ onTextSelection, uploadedFile, targetPage }: PDFViewerProps) => {
  return (
    <div className="flex-1 bg-background border border-border rounded-lg overflow-hidden">
      <AdobePDFViewer
        file={uploadedFile}
        onTextSelection={onTextSelection}
        targetPage={targetPage}
      />
    </div>
  );
};

export default PDFViewer;