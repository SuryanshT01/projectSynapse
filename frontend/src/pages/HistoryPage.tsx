import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArrowLeft, FileText, MessageSquare, Volume2, Calendar, Play, PauseCircle } from 'lucide-react';

interface HistoryItem {
  id: string;
  type: 'summary' | 'insight' | 'audio';
  title: string;
  content: string;
  timestamp: string;
  pdfName: string;
  audioUrl?: string;
  duration?: string;
}

interface PDFMetadata {
  name: string;
  uploadDate: string;
  size: string;
}

const HistoryPage = () => {
  const navigate = useNavigate();
  const [selectedPDF, setSelectedPDF] = useState<string>('Annual Report 2023.pdf');
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  
  // Mock data - this would come from backend
  const [historyItems] = useState<HistoryItem[]>([
    {
      id: '1',
      type: 'summary',
      title: 'Executive Summary',
      content: 'This annual report highlights the company\'s strong financial performance with 15% revenue growth, expansion into new markets, and strategic partnerships that position us for continued success in the upcoming fiscal year.',
      timestamp: '2024-01-15T10:30:00Z',
      pdfName: 'Annual Report 2023.pdf'
    },
    {
      id: '2',
      type: 'summary',
      title: 'Financial Overview',
      content: 'Revenue increased by 15% year-over-year, with strong performance across all business segments. Operating margins improved by 2.3% due to operational efficiencies and cost optimization initiatives.',
      timestamp: '2024-01-15T10:15:00Z',
      pdfName: 'Annual Report 2023.pdf'
    },
    {
      id: '3',
      type: 'insight',
      title: 'Market Expansion Opportunity',
      content: 'The European market shows significant growth potential, with 40% untapped customer base in the enterprise segment. Recommend prioritizing German and French markets for Q2 expansion.',
      timestamp: '2024-01-15T09:45:00Z',
      pdfName: 'Annual Report 2023.pdf'
    },
    {
      id: '4',
      type: 'insight',
      title: 'Competitive Analysis Gap',
      content: 'Current analysis lacks depth in competitor pricing strategies. Consider conducting detailed pricing comparison study to identify competitive advantages and pricing optimization opportunities.',
      timestamp: '2024-01-15T09:30:00Z',
      pdfName: 'Annual Report 2023.pdf'
    },
    {
      id: '5',
      type: 'audio',
      title: 'Financial Highlights Podcast',
      content: 'A 5-minute audio summary covering the key financial metrics, growth drivers, and outlook for the next fiscal year.',
      timestamp: '2024-01-15T09:00:00Z',
      pdfName: 'Annual Report 2023.pdf',
      audioUrl: '/audio/annual-highlights.mp3',
      duration: '5:23'
    },
    {
      id: '6',
      type: 'audio',
      title: 'Strategic Initiatives Deep Dive',
      content: 'Detailed audio analysis of the company\'s three main strategic initiatives and their projected impact on future growth.',
      timestamp: '2024-01-15T08:45:00Z',
      pdfName: 'Annual Report 2023.pdf',
      audioUrl: '/audio/strategic-deep-dive.mp3',
      duration: '12:45'
    },
    {
      id: '7',
      type: 'insight',
      title: 'Consumer Behavior Trends',
      content: 'Research reveals shift toward mobile-first purchasing decisions, with 65% of customers preferring mobile checkout processes. This trend accelerated by 25% post-pandemic.',
      timestamp: '2024-01-14T16:20:00Z',
      pdfName: 'Market Research.pdf'
    },
    {
      id: '8',
      type: 'summary',
      title: 'Market Analysis Overview',
      content: 'Comprehensive analysis of market trends shows strong growth in digital channels, changing consumer preferences, and emerging competitive threats from fintech startups.',
      timestamp: '2024-01-14T15:30:00Z',
      pdfName: 'Market Research.pdf'
    },
    {
      id: '9',
      type: 'audio',
      title: 'Market Trends Briefing',
      content: 'Weekly market trends briefing highlighting key developments, consumer insights, and strategic recommendations.',
      timestamp: '2024-01-14T14:15:00Z',
      pdfName: 'Market Research.pdf',
      audioUrl: '/audio/market-briefing.mp3',
      duration: '8:12'
    }
  ]);

  // Mock PDF library with metadata
  const [pdfLibrary] = useState<PDFMetadata[]>([
    { name: 'Annual Report 2023.pdf', uploadDate: '2024-01-15', size: '2.4 MB' },
    { name: 'Market Research.pdf', uploadDate: '2024-01-14', size: '1.8 MB' },
    { name: 'Financial Analysis.pdf', uploadDate: '2024-01-13', size: '3.1 MB' },
    { name: 'Technical Documentation.pdf', uploadDate: '2024-01-12', size: '5.2 MB' }
  ]);

  const handleBackToReader = () => {
    navigate('/reader');
  };

  const handlePDFSelect = (pdfName: string) => {
    setSelectedPDF(pdfName);
  };

  const handleAudioPlay = (audioId: string) => {
    if (playingAudio === audioId) {
      setPlayingAudio(null);
    } else {
      setPlayingAudio(audioId);
    }
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Get current PDF metadata
  const currentPDF = pdfLibrary.find(pdf => pdf.name === selectedPDF);

  // Filter history items by type for selected PDF
  const summaryItems = historyItems.filter(item => item.pdfName === selectedPDF && item.type === 'summary');
  const insightItems = historyItems.filter(item => item.pdfName === selectedPDF && item.type === 'insight');
  const audioItems = historyItems.filter(item => item.pdfName === selectedPDF && item.type === 'audio');

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-border bg-card">
        <div className="flex items-center justify-between px-6 py-4">
          {/* Left: Logo/Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">DocInsight</span>
          </div>

          {/* Center: Current PDF Info */}
          <div className="flex flex-col items-center">
            <h2 className="text-lg font-semibold text-foreground">{currentPDF?.name}</h2>
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <span>Uploaded: {currentPDF?.uploadDate}</span>
              <span>Size: {currentPDF?.size}</span>
            </div>
          </div>

          {/* Right: Back Button */}
          <Button 
            variant="outline" 
            onClick={handleBackToReader}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Reader</span>
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Column - PDF Navigation */}
        <div className="w-64 border-r border-border bg-muted/30">
          <div className="p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground">PDF Library</h3>
          </div>
          <ScrollArea className="h-full">
            <div className="p-2">
              {pdfLibrary.map((pdf) => (
                <div
                  key={pdf.name}
                  className={`p-3 rounded-md cursor-pointer transition-colors mb-2 ${
                    selectedPDF === pdf.name
                      ? 'bg-primary text-primary-foreground' 
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => handlePDFSelect(pdf.name)}
                >
                  <div className="flex items-start space-x-2">
                    <FileText className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{pdf.name}</p>
                      <p className="text-xs opacity-75">{pdf.size}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Right Content Area - Three Columns */}
        <div className="flex-1 grid grid-cols-3 gap-1">
          {/* Summary Column */}
          <div className="border-r border-border bg-card">
            <div className="p-4 border-b border-border">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">Summaries</h3>
                <span className="text-sm text-muted-foreground">({summaryItems.length})</span>
              </div>
            </div>
            <ScrollArea className="h-full">
              <div className="p-4 space-y-4">
                {summaryItems.length === 0 ? (
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">No summaries yet</p>
                  </div>
                ) : (
                  summaryItems.map((item) => (
                    <Card key={item.id} className="cursor-pointer hover:shadow-md transition-shadow">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">{item.title}</CardTitle>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(item.timestamp)}</span>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">{item.content}</p>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Insights Column */}
          <div className="border-r border-border bg-card">
            <div className="p-4 border-b border-border">
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">Insights</h3>
                <span className="text-sm text-muted-foreground">({insightItems.length})</span>
              </div>
            </div>
            <ScrollArea className="h-full">
              <div className="p-4 space-y-4">
                {insightItems.length === 0 ? (
                  <div className="text-center py-8">
                    <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">No insights yet</p>
                  </div>
                ) : (
                  insightItems.map((item) => (
                    <Card key={item.id} className="cursor-pointer hover:shadow-md transition-shadow">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">{item.title}</CardTitle>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(item.timestamp)}</span>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">{item.content}</p>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Audio Column */}
          <div className="bg-card">
            <div className="p-4 border-b border-border">
              <div className="flex items-center space-x-2">
                <Volume2 className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">Audio</h3>
                <span className="text-sm text-muted-foreground">({audioItems.length})</span>
              </div>
            </div>
            <ScrollArea className="h-full">
              <div className="p-4 space-y-4">
                {audioItems.length === 0 ? (
                  <div className="text-center py-8">
                    <Volume2 className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">No audio yet</p>
                  </div>
                ) : (
                  audioItems.map((item) => (
                    <Card key={item.id} className="cursor-pointer hover:shadow-md transition-shadow">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">{item.title}</CardTitle>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                            <Calendar className="w-3 h-3" />
                            <span>{formatDate(item.timestamp)}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">{item.duration}</span>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground mb-3">{item.content}</p>
                        <div className="flex items-center space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAudioPlay(item.id);
                            }}
                            className="flex items-center space-x-1"
                          >
                            {playingAudio === item.id ? (
                              <PauseCircle className="w-4 h-4" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                            <span>{playingAudio === item.id ? 'Pause' : 'Play'}</span>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;