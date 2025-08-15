import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { History, Home, Library, FileText } from 'lucide-react';

interface RightSidebarProps {
  onPDFSelect?: (pdfId: string) => void;
}

const RightSidebar = ({ onPDFSelect }: RightSidebarProps) => {
  const navigate = useNavigate();
  const [isHomeClicked, setIsHomeClicked] = useState(false);

  // Mock PDF data
  const pdfDocuments = [
    { id: '1', name: 'Annual Report 2023.pdf', uploadDate: '2024-01-15' },
    { id: '2', name: 'Project Proposal.pdf', uploadDate: '2024-01-14' },
    { id: '3', name: 'Financial Analysis.pdf', uploadDate: '2024-01-13' },
    { id: '4', name: 'Market Research.pdf', uploadDate: '2024-01-12' },
  ];

  const handleHistoryClick = () => {
    navigate('/history');
  };

  const handleHomeClick = () => {
    setIsHomeClicked(true);
    navigate('/');
    // Reset the clicked state after navigation
    setTimeout(() => setIsHomeClicked(false), 200);
  };

  const handlePDFSelect = (pdfId: string) => {
    onPDFSelect?.(pdfId);
  };

  return (
    <div className="w-[180px] h-full bg-muted border-l border-sidebar-border flex flex-col p-4 space-y-3">
      <Button 
        onClick={handleHistoryClick}
        className="w-full justify-start"
        variant="default"
      >
        <History className="w-4 h-4 mr-2" />
        History
      </Button>
      
      <Button 
        onClick={handleHomeClick}
        className="w-full justify-start"
        variant={isHomeClicked ? "secondary" : "ghost"}
      >
        <Home className="w-4 h-4 mr-2" />
        Home
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            className="w-full justify-start"
            variant="ghost"
          >
            <Library className="w-4 h-4 mr-2" />
            Library
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56 bg-background">
          {pdfDocuments.map((doc) => (
            <DropdownMenuItem
              key={doc.id}
              onClick={() => handlePDFSelect(doc.id)}
              className="flex items-start space-x-2 p-3"
            >
              <FileText className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate" title={doc.name}>
                  {doc.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(doc.uploadDate).toLocaleDateString()}
                </div>
              </div>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default RightSidebar;