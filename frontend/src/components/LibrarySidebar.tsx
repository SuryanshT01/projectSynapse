import { useState } from 'react';
import { FileText, Hash, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PDFSection {
  id: string;
  title: string;
  page: number;
  level: number; // 1 for main headings, 2 for subheadings, etc.
}

interface LibrarySidebarProps {
  selectedPDF?: string;
  onSectionSelect?: (sectionId: string) => void;
}

const LibrarySidebar = ({ selectedPDF, onSectionSelect }: LibrarySidebarProps) => {
  // Mock PDF sections data - this would come from backend
  const [pdfSections] = useState<PDFSection[]>([
    { id: '1', title: 'Executive Summary', page: 1, level: 1 },
    { id: '2', title: 'Introduction', page: 2, level: 1 },
    { id: '3', title: 'Market Overview', page: 4, level: 1 },
    { id: '4', title: 'Current Market Trends', page: 5, level: 2 },
    { id: '5', title: 'Competitive Analysis', page: 7, level: 2 },
    { id: '6', title: 'Financial Performance', page: 10, level: 1 },
    { id: '7', title: 'Revenue Analysis', page: 11, level: 2 },
    { id: '8', title: 'Cost Structure', page: 13, level: 2 },
    { id: '9', title: 'Future Projections', page: 15, level: 1 },
    { id: '10', title: 'Conclusion', page: 18, level: 1 },
  ]);

  const handleSectionClick = (sectionId: string) => {
    onSectionSelect?.(sectionId);
  };

  return (
    <div className="w-[200px] h-full bg-muted border-r border-sidebar-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        {selectedPDF ? (
          <>
            <h2 className="font-semibold text-foreground">Contents</h2>
            <p className="text-sm text-muted-foreground">{pdfSections.length} sections</p>
          </>
        ) : (
          <>
            <h2 className="font-semibold text-foreground">Navigation</h2>
            <p className="text-sm text-muted-foreground">Select a PDF to view sections</p>
          </>
        )}
      </div>

      {/* Sections List */}
      <div className="flex-1 overflow-y-auto">
        {!selectedPDF ? (
          <div className="p-4 text-center">
            <Hash className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No document selected</p>
          </div>
        ) : (
          <div className="p-2">
            {pdfSections.map((section) => (
              <Button
                key={section.id}
                variant="ghost"
                className={`w-full justify-start mb-1 h-auto p-2 text-left hover:bg-accent ${
                  section.level === 2 ? 'ml-4' : ''
                }`}
                onClick={() => handleSectionClick(section.id)}
              >
                <div className="flex items-start space-x-2 flex-1 min-w-0">
                  <Hash className="w-3 h-3 text-primary mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm truncate ${
                      section.level === 1 ? 'font-medium' : 'font-normal'
                    }`} title={section.title}>
                      {section.title}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Page {section.page}
                    </div>
                  </div>
                  <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0 opacity-0 group-hover:opacity-100" />
                </div>
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LibrarySidebar;