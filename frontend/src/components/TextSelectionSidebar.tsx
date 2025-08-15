import { useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

interface TextSelectionSidebarProps {
  isOpen: boolean;
  selectedText: string;
  onClose: () => void;
  onPromptSubmit: (prompt: string, selectedText: string) => void;
}

const TextSelectionSidebar = ({ isOpen, selectedText, onClose, onPromptSubmit }: TextSelectionSidebarProps) => {
  const [prompt, setPrompt] = useState('');
  const [activeAccordion, setActiveAccordion] = useState<string>('');

  // Initialize prompt with selected text when sidebar opens
  useState(() => {
    if (isOpen && selectedText) {
      setPrompt(selectedText);
    }
  });

  const handleSubmit = () => {
    onPromptSubmit(prompt, selectedText);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />
      
      {/* Sliding Sidebar */}
      <div className={`fixed right-0 top-0 h-full w-80 bg-background border-l border-border z-50 transform transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* Header with close button */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h3 className="font-medium text-foreground">Selected Text</h3>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>

          {/* Accordion Section */}
          <div className="flex-1 p-4 overflow-y-auto">
            <Accordion 
              type="single" 
              collapsible 
              value={activeAccordion}
              onValueChange={setActiveAccordion}
            >
              <AccordionItem value="related-content">
                <AccordionTrigger>Related Content</AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>Related snippets from uploaded PDFs will appear here...</p>
                    <div className="bg-muted p-3 rounded-md">
                      <p className="font-medium text-foreground mb-1">Similar section found:</p>
                      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit...</p>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="insight-generation">
                <AccordionTrigger>Insight Generation</AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>AI-generated insights, contradictions, and examples will appear here...</p>
                    <div className="bg-muted p-3 rounded-md">
                      <p className="font-medium text-foreground mb-1">Key Insight:</p>
                      <p>This text suggests a correlation between...</p>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="audio-podcast">
                <AccordionTrigger>Audio / Podcast</AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>Audio and podcast links related to this text will appear here...</p>
                    <div className="bg-muted p-3 rounded-md">
                      <p className="font-medium text-foreground mb-1">Related Podcast:</p>
                      <p>Episode 42: Understanding the implications of...</p>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>

          {/* Prompt Input at bottom */}
          <div className="p-4 border-t border-border bg-card">
            <label className="text-sm font-medium text-foreground mb-2 block">
              Edit your query (optional)
            </label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Add or modify your prompt..."
              className="mb-3"
              rows={3}
            />
            <Button 
              onClick={handleSubmit}
              className="w-full"
              disabled={!prompt.trim()}
            >
              Submit Query
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};

export default TextSelectionSidebar;