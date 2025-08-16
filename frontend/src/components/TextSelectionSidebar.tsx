// src/components/TextSelectionSidebar.tsx
import { ChevronLeft, FileText, Bot, Mic, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { RelatedSection, Insights } from '@/types/analysis';
import { Skeleton } from '@/components/ui/skeleton';

interface TextSelectionSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  selectedText: string;
  relatedSections: RelatedSection[];
  insights: Insights | null;
  podcastUrl: string | null;
  isLoadingRelated: boolean;
  isLoadingInsights: boolean;
  isLoadingPodcast: boolean;
  error: string | null;
}

// A small component for loading states
const LoadingSpinner = () => (
  <div className="flex items-center space-x-2 p-2">
    <Skeleton className="h-4 w-4 rounded-full" />
    <Skeleton className="h-4 w-[200px]" />
  </div>
);

const TextSelectionSidebar = ({
  isOpen, onClose, selectedText,
  relatedSections, insights, podcastUrl,
  isLoadingRelated, isLoadingInsights, isLoadingPodcast,
  error
}: TextSelectionSidebarProps) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 z-40 backdrop-blur-sm" onClick={onClose} />
      
      {/* Sliding Sidebar */}
      <div className={`fixed right-0 top-0 h-full w-96 bg-background border-l border-border z-50 transform transition-transform duration-300 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-start justify-between p-4 border-b border-border">
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">Analysis</h3>
              <p className="text-xs text-muted-foreground italic truncate" title={selectedText}>
                Based on: "{selectedText}"
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 flex-shrink-0">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive-foreground">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-5 w-5 mt-0.5" />
                <div>
                  <p className="font-semibold">Analysis Failed</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Accordion Section */}
          <div className="flex-1 p-4 overflow-y-auto">
            <Accordion type="multiple" defaultValue={['related-content']} className="w-full">
              
              <AccordionItem value="related-content">
                <AccordionTrigger><FileText className="mr-2 h-4 w-4" /> Related Content</AccordionTrigger>
                <AccordionContent>
                  {isLoadingRelated && <LoadingSpinner />}
                  {!isLoadingRelated && relatedSections.length === 0 && <p className="text-sm text-muted-foreground p-2">No related sections found.</p>}
                  <div className="space-y-3">
                    {relatedSections.map((section, index) => (
                      <div key={index} className="bg-muted p-3 rounded-md text-sm">
                        <p className="font-semibold text-foreground truncate" title={section.doc_name}>{section.doc_name}</p>
                        <p className="text-xs text-muted-foreground mb-1">Page {section.page} - {section.section_title}</p>
                        <p className="text-foreground/80 leading-relaxed">"{section.snippet}"</p>
                      </div>
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="insight-generation">
                <AccordionTrigger><Bot className="mr-2 h-4 w-4" /> AI Insights</AccordionTrigger>
                <AccordionContent>
                  {isLoadingInsights && <LoadingSpinner />}
                  {!isLoadingInsights && !insights && <p className="text-sm text-muted-foreground p-2">Insights will appear here once generated.</p>}
                  {insights && (
                    <div className="bg-muted p-3 rounded-md text-sm space-y-2">
                      {Object.entries(insights).map(([key, value]) => (
                        <div key={key}>
                          <h4 className="font-semibold capitalize text-foreground">{key.replace(/_/g, ' ')}</h4>
                          <p className="text-foreground/80 whitespace-pre-wrap">{typeof value === 'object' ? JSON.stringify(value, null, 2) : value}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="audio-podcast">
                <AccordionTrigger><Mic className="mr-2 h-4 w-4" /> Audio Summary</AccordionTrigger>
                <AccordionContent>
                  {isLoadingPodcast && <LoadingSpinner />}
                  {!isLoadingPodcast && !podcastUrl && <p className="text-sm text-muted-foreground p-2">An audio version will be available shortly.</p>}
                  {podcastUrl && (
                    <div className="p-2">
                      <audio controls src={podcastUrl} className="w-full">
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  )}
                </AccordionContent>
              </AccordionItem>

            </Accordion>
          </div>
        </div>
      </div>
    </>
  );
};

export default TextSelectionSidebar;