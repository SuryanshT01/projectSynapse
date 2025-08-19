// src/components/TextSelectionSidebar.tsx - Updated with better error handling

import { ChevronLeft, FileText, Bot, Mic, AlertTriangle, RefreshCw, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { RelatedSection, Insights } from '@/types/analysis';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';

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
  onSectionClick?: (section: RelatedSection) => void;
  onRetry?: () => void; // Optional retry function
}

// Enhanced loading spinner with text
const LoadingSpinner = ({ text = "Loading..." }: { text?: string }) => (
  <div className="flex items-center space-x-3 p-4">
    <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
    <div className="space-y-2">
      <Skeleton className="h-4 w-[200px]" />
      <span className="text-sm text-muted-foreground">{text}</span>
    </div>
  </div>
);

// Error display component
const ErrorDisplay = ({ 
  title, 
  message, 
  onRetry, 
  onDismiss 
}: { 
  title: string; 
  message: string; 
  onRetry?: () => void;
  onDismiss?: () => void;
}) => (
  <Alert variant="destructive" className="m-4">
    <AlertTriangle className="h-4 w-4" />
    <AlertDescription>
      <div className="space-y-2">
        <div className="font-semibold">{title}</div>
        <div className="text-sm">{message}</div>
        <div className="flex space-x-2 mt-3">
          {onRetry && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onRetry}
              className="h-8"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
          {onDismiss && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onDismiss}
              className="h-8"
            >
              <X className="h-3 w-3 mr-1" />
              Dismiss
            </Button>
          )}
        </div>
      </div>
    </AlertDescription>
  </Alert>
);

// Audio player component with enhanced controls
const AudioPlayer = ({ src, title = "Podcast Audio" }: { src: string; title?: string }) => {
  return (
    <div className="p-4 space-y-3">
      <div className="text-sm font-medium text-foreground">{title}</div>
      <audio 
        controls 
        src={src} 
        className="w-full"
        preload="metadata"
      >
        <track kind="captions" />
        Your browser does not support the audio element.
      </audio>
      <div className="text-xs text-muted-foreground">
        Right-click to download or save the audio file
      </div>
    </div>
  );
};

const TextSelectionSidebar = ({
  isOpen, 
  onClose, 
  selectedText,
  relatedSections, 
  insights, 
  podcastUrl,
  isLoadingRelated, 
  isLoadingInsights, 
  isLoadingPodcast,
  error,
  onSectionClick,
  onRetry
}: TextSelectionSidebarProps) => {
  if (!isOpen) return null;

  // Determine which sections should be expanded by default
  const getDefaultOpenSections = () => {
    const sections = [];
    
    // Always open related content first
    sections.push('related-content');
    
    // Open insights if available or loading
    if (insights || isLoadingInsights) {
      sections.push('insight-generation');
    }
    
    // Open audio if available or loading
    if (podcastUrl || isLoadingPodcast) {
      sections.push('audio-podcast');
    }
    
    return sections;
  };

  const handleErrorDismiss = () => {
    // This would be handled by the parent component
    if (onRetry) {
      onRetry();
    }
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    }
  };

  // Check if any operation is in progress
  const isAnyLoading = isLoadingRelated || isLoadingInsights || isLoadingPodcast;
  const hasAnyContent = relatedSections.length > 0 || insights || podcastUrl;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/30 z-40 backdrop-blur-sm" 
        onClick={onClose} 
      />
      
      {/* Sliding Sidebar */}
      <div className={`fixed right-0 top-0 h-full w-96 bg-background border-l border-border z-50 transform transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          
          {/* Header */}
          <div className="flex items-start justify-between p-4 border-b border-border bg-muted/30">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground">AI Analysis</h3>
              <p className="text-xs text-muted-foreground italic truncate mt-1" title={selectedText}>
                "{selectedText}"
              </p>
              {isAnyLoading && (
                <div className="mt-2 flex items-center text-xs text-blue-600">
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                  Processing...
                </div>
              )}
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={onClose} 
              className="h-8 w-8 flex-shrink-0 ml-2"
              title="Close analysis panel"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>

          {/* Global Error Display */}
          {error && (
            <ErrorDisplay
              title="Analysis Failed"
              message={error}
              onRetry={onRetry ? handleRetry : undefined}
              onDismiss={handleErrorDismiss}
            />
          )}

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            
            {/* Loading state when first starting */}
            {isAnyLoading && !hasAnyContent && !error && (
              <div className="p-4">
                <LoadingSpinner text="Starting AI analysis..." />
              </div>
            )}

            {/* Main Content Accordion */}
            <Accordion 
              type="multiple" 
              defaultValue={getDefaultOpenSections()} 
              className="w-full"
            >
              
              {/* Related Content Section */}
              <AccordionItem value="related-content">
                <AccordionTrigger className="px-4 py-3 hover:bg-muted/50">
                  <div className="flex items-center">
                    <FileText className="mr-2 h-4 w-4" />
                    <span>Related Content</span>
                    {isLoadingRelated && <RefreshCw className="ml-2 h-3 w-3 animate-spin" />}
                    {relatedSections.length > 0 && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        {relatedSections.length}
                      </span>
                    )}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-2">
                  {isLoadingRelated && (
                    <LoadingSpinner text="Finding related content..." />
                  )}
                  
                  {!isLoadingRelated && relatedSections.length === 0 && (
                    <div className="p-4 text-center text-muted-foreground">
                      <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No related sections found.</p>
                    </div>
                  )}
                  
                  <div className="space-y-3 px-4">
                    {relatedSections.map((section, index) => (
                      <button
                        key={index}
                        className="bg-muted/60 p-3 rounded-md text-sm w-full text-left hover:bg-primary/10 transition-colors border border-transparent hover:border-primary/20"
                        onClick={() => onSectionClick && onSectionClick(section)}
                      >
                        <div className="space-y-2">
                          <p className="font-semibold text-foreground truncate" title={section.doc_name}>
                            {section.doc_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Page {section.page} • {section.section_title}
                          </p>
                          <p className="text-foreground/80 leading-relaxed line-clamp-3">
                            "{section.snippet}"
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* AI Insights Section */}
              <AccordionItem value="insight-generation">
                <AccordionTrigger className="px-4 py-3 hover:bg-muted/50">
                  <div className="flex items-center">
                    <Bot className="mr-2 h-4 w-4" />
                    <span>AI Insights</span>
                    {isLoadingInsights && <RefreshCw className="ml-2 h-3 w-3 animate-spin" />}
                    {insights && (
                      <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Ready
                      </span>
                    )}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-2">
                  {isLoadingInsights && (
                    <LoadingSpinner text="Generating AI insights..." />
                  )}
                  
                  {!isLoadingInsights && !insights && (
                    <div className="p-4 text-center text-muted-foreground">
                      <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">AI insights will appear here once generated.</p>
                    </div>
                  )}
                  
                  {insights && (
                    <div className="px-4 space-y-4">
                      {Object.entries(insights).map(([key, value]) => (
                        <div key={key} className="bg-muted/60 p-4 rounded-md">
                          <h4 className="font-semibold capitalize text-foreground mb-2 text-sm">
                            {key.replace(/_/g, ' ')}
                          </h4>
                          <div className="text-sm text-foreground/80 whitespace-pre-wrap leading-relaxed">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </AccordionContent>
              </AccordionItem>

              {/* Audio Podcast Section */}
              <AccordionItem value="audio-podcast">
                <AccordionTrigger className="px-4 py-3 hover:bg-muted/50">
                  <div className="flex items-center">
                    <Mic className="mr-2 h-4 w-4" />
                    <span>Audio Summary</span>
                    {isLoadingPodcast && <RefreshCw className="ml-2 h-3 w-3 animate-spin" />}
                    {podcastUrl && (
                      <span className="ml-2 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                        Ready
                      </span>
                    )}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-2">
                  {isLoadingPodcast && (
                    <LoadingSpinner text="Generating audio summary..." />
                  )}
                  
                  {!isLoadingPodcast && !podcastUrl && (
                    <div className="p-4 text-center text-muted-foreground">
                      <Mic className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">Audio summary will be available shortly.</p>
                    </div>
                  )}
                  
                  {podcastUrl && (
                    <AudioPlayer src={podcastUrl} title="AI-Generated Audio Summary" />
                  )}
                </AccordionContent>
              </AccordionItem>

            </Accordion>
          </div>

          {/* Footer with helpful info */}
          <div className="border-t border-border p-3 bg-muted/20">
            <div className="text-xs text-muted-foreground text-center">
              {isAnyLoading ? (
                "Processing your request..."
              ) : hasAnyContent ? (
                "Analysis complete • Close this panel to cancel any ongoing requests"
              ) : (
                "Select text to start analysis"
              )}
            </div>
          </div>
          
        </div>
      </div>
    </>
  );
};

export default TextSelectionSidebar;