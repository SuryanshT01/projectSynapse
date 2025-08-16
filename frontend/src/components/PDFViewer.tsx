// src/components/PDFViewer.tsx
import AdobePDFViewer from './AdobePDFViewer';

interface PDFViewerProps {
  onTextSelection: (text: string) => void;
  uploadedFile: File | null;
}

const PDFViewer = ({ onTextSelection, uploadedFile }: PDFViewerProps) => {
  return (
    <div className="flex-1 bg-background border border-border rounded-lg overflow-hidden">
      <AdobePDFViewer
        file={uploadedFile}
        onTextSelection={onTextSelection}
      />
    </div>
  );
};

export default PDFViewer;