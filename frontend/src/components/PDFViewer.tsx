import { File, ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PDFViewerProps {
  selectedPDF?: string;
  onTextSelection: (text: string) => void;
}

const PDFViewer = ({ selectedPDF, onTextSelection }: PDFViewerProps) => {
  // Simulate text selection - in real app this would come from backend PDF viewer
  const handleTextSelection = () => {
    const mockSelectedText = "This is the selected text from the PDF document that the user highlighted.";
    onTextSelection(mockSelectedText);
  };

  return (
    <div className="flex-1 bg-background border border-border rounded-lg overflow-hidden">
      {selectedPDF ? (
        <div className="h-full flex flex-col">
          {/* PDF Viewer Header */}
          <div className="flex items-center justify-between p-4 border-b border-border bg-card">
            <div className="flex items-center space-x-2">
              <File className="w-5 h-5 text-primary" />
              <span className="font-medium text-foreground">Document Viewer</span>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <ZoomOut className="w-4 h-4" />
              </Button>
              <span className="text-sm text-muted-foreground px-2">100%</span>
              <Button variant="outline" size="sm">
                <ZoomIn className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* PDF Content Placeholder */}
          <div className="flex-1 bg-gray-50 flex items-center justify-center relative">
            <div className="text-center space-y-4">
              <div className="w-32 h-40 bg-white border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center mx-auto">
                <File className="w-16 h-16 text-gray-400" />
              </div>
              <div>
                <p className="text-lg font-medium text-gray-600 mb-2">PDF Viewer Placeholder</p>
                <p className="text-sm text-gray-500 mb-4">
                  Backend will inject the actual PDF viewer here
                </p>
                <Button onClick={handleTextSelection} variant="outline">
                  Simulate Text Selection
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="h-full flex items-center justify-center">
          <div className="text-center space-y-4">
            <File className="w-16 h-16 text-muted-foreground mx-auto" />
            <div>
              <h3 className="text-lg font-medium text-foreground mb-2">No Document Selected</h3>
              <p className="text-muted-foreground">
                Select a PDF from your library or upload a new document to get started
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;