import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Quote } from 'lucide-react';

interface ModalPromptProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (query: string) => void;
  selectedText: string;
}

const ModalPrompt = ({ isOpen, onClose, onSubmit, selectedText }: ModalPromptProps) => {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    onSubmit(query);
    setQuery('');
  };

  const handleClose = () => {
    setQuery('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Quote className="w-5 h-5 text-primary" />
            <span>Query Selected Text</span>
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Selected Text Display */}
          <div>
            <Label className="text-sm font-medium text-foreground">Selected Text:</Label>
            <div className="mt-2 p-3 bg-muted rounded-lg border">
              <p className="text-sm text-foreground italic">"{selectedText}"</p>
            </div>
          </div>

          {/* Query Input */}
          <div>
            <Label htmlFor="query" className="text-sm font-medium text-foreground">
              Your Query (Optional)
            </Label>
            <Textarea
              id="query"
              placeholder="Ask a question about the selected text, request a summary, or leave empty for default analysis..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="mt-2 min-h-[100px] resize-none"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Leave empty to generate insights based on the selected text alone
            </p>
          </div>
        </div>

        <DialogFooter className="space-x-2">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>
            Generate Insights
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ModalPrompt;