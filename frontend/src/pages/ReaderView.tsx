// src/pages/ReaderView.tsx - Updated with request cancellation

import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import LibrarySidebar from '@/components/LibrarySidebar';
import PDFViewer from '@/components/PDFViewer';
import RightSidebar from '@/components/RightSidebar';
import TextSelectionSidebar from '@/components/TextSelectionSidebar';
import { RelatedSection, Insights } from '@/types/analysis';

const ReaderView = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  // State for the Text Selection Sidebar
  const [isTextSidebarOpen, setIsTextSidebarOpen] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  
  // State for the analysis results
  const [relatedSections, setRelatedSections] = useState<RelatedSection[]>([]);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [podcastUrl, setPodcastUrl] = useState<string | null>(null);

  // Loading and error states for each part of the analysis
  const [isLoadingRelated, setIsLoadingRelated] = useState(false);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [isLoadingPodcast, setIsLoadingPodcast] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New states for handling PDF and section clicks
  const [targetPage, setTargetPage] = useState<number | null>(null);
  const [currentDocName, setCurrentDocName] = useState<string>('');

  // AbortController refs for cancelling requests
  const sectionsAbortController = useRef<AbortController | null>(null);
  const insightsAbortController = useRef<AbortController | null>(null);
  const podcastAbortController = useRef<AbortController | null>(null);

  useEffect(() => {
    if (location.state?.uploadedFile) {
      setUploadedFile(location.state.uploadedFile);
    }
  }, [location.state]);

  // Cleanup function to abort all active requests
  const cancelAllRequests = useCallback(() => {
    console.log('Cancelling all active requests...');
    
    if (sectionsAbortController.current) {
      sectionsAbortController.current.abort();
      sectionsAbortController.current = null;
    }
    
    if (insightsAbortController.current) {
      insightsAbortController.current.abort();
      insightsAbortController.current = null;
    }
    
    if (podcastAbortController.current) {
      podcastAbortController.current.abort();
      podcastAbortController.current = null;
    }

    // Reset loading states
    setIsLoadingRelated(false);
    setIsLoadingInsights(false);
    setIsLoadingPodcast(false);
  }, []);

  const startAnalysisFlow = useCallback(async (text: string) => {
    // Cancel any existing requests first
    cancelAllRequests();
    
    // Reset all states for a new analysis
    setIsTextSidebarOpen(true);
    setRelatedSections([]);
    setInsights(null);
    setPodcastUrl(null);
    setError(null);
    
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080';

    try {
      // Step 1: Fetch Related Sections
      setIsLoadingRelated(true);
      
      // Create new AbortController for sections request
      const sectionsController = new AbortController();
      sectionsAbortController.current = sectionsController;
      
      const sectionsResponse = await fetch(`${apiUrl}/api/related-sections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: text }),
        signal: sectionsController.signal,
      });

      // Check if request was aborted
      if (sectionsController.signal.aborted) {
        console.log('Sections request was aborted');
        return;
      }
      
      if (!sectionsResponse.ok) throw new Error('Failed to fetch related sections.');
      
      const sections: RelatedSection[] = await sectionsResponse.json();
      setRelatedSections(sections);
      setIsLoadingRelated(false);
      sectionsAbortController.current = null;
      
      const relatedSnippets = sections.map(s => s.snippet);

      // Step 2: Fetch Insights (depends on related sections)
      setIsLoadingInsights(true);
      
      // Create new AbortController for insights request
      const insightsController = new AbortController();
      insightsAbortController.current = insightsController;
      
      const insightsResponse = await fetch(`${apiUrl}/api/insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: text, related_snippets: relatedSnippets }),
        signal: insightsController.signal,
      });

      // Check if request was aborted
      if (insightsController.signal.aborted) {
        console.log('Insights request was aborted');
        return;
      }
      
      if (!insightsResponse.ok) throw new Error('Failed to generate insights.');
      
      const insightData: Insights = await insightsResponse.json();
      setInsights(insightData);
      setIsLoadingInsights(false);
      insightsAbortController.current = null;

      // Step 3: Fetch Podcast (also depends on related sections)
      setIsLoadingPodcast(true);
      
      // Create new AbortController for podcast request
      const podcastController = new AbortController();
      podcastAbortController.current = podcastController;
      
      const podcastResponse = await fetch(`${apiUrl}/api/podcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: text, related_snippets: relatedSnippets }),
        signal: podcastController.signal,
      });

      // Check if request was aborted
      if (podcastController.signal.aborted) {
        console.log('Podcast request was aborted');
        return;
      }
      
      if (!podcastResponse.ok) {
        // Handle specific error cases
        if (podcastResponse.status === 499) {
          console.log('Podcast request was cancelled by server');
          return;
        } else if (podcastResponse.status === 503) {
          throw new Error('Text-to-speech service is currently unavailable. Please check configuration.');
        } else {
          throw new Error('Failed to generate podcast audio.');
        }
      }
      
      const audioBlob = await podcastResponse.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      setPodcastUrl(audioUrl);
      setIsLoadingPodcast(false);
      podcastAbortController.current = null;

    } catch (err: any) {
      // Handle different types of errors
      if (err.name === 'AbortError') {
        console.log('Request was aborted:', err.message);
        return; // Don't set error state for aborted requests
      }
      
      console.error("Analysis flow failed:", err);
      setError(err.message || 'An unknown error occurred during analysis.');
      
      // Stop all loading indicators on error
      setIsLoadingRelated(false);
      setIsLoadingInsights(false);
      setIsLoadingPodcast(false);
      
      // Clear abort controllers
      sectionsAbortController.current = null;
      insightsAbortController.current = null;
      podcastAbortController.current = null;
    }
  }, [cancelAllRequests]);

  const handleTextSelection = useCallback((text: string) => {
    // This is the trigger for the entire journey flow
    if (text && text.length > 10) { // Add a minimum length to avoid accidental triggers
      setSelectedText(text);
      startAnalysisFlow(text);
    }
  }, [startAnalysisFlow]);

  const handleSectionClick = useCallback(async (section: RelatedSection) => {
    if (!section.pdf_available || !section.pdf_url) {
      setError('PDF not available for this section.');
      return;
    }
    
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080';
    
    try {
      // Fetch the PDF from backend
      const response = await fetch(`${apiUrl}${section.pdf_url}`);
      if (!response.ok) throw new Error('Failed to fetch PDF');
      
      const blob = await response.blob();
      const newFile = new File([blob], section.doc_name, { type: 'application/pdf' });
      setUploadedFile(newFile);
      setCurrentDocName(section.doc_name);
      setTargetPage(section.page);
      setIsTextSidebarOpen(false); // Optionally close sidebar
    } catch (err: any) {
      setError(err.message || 'Failed to load PDF');
    }
  }, []);

  // Handle sidebar close with request cancellation
  const handleSidebarClose = useCallback(() => {
    console.log('Sidebar closing, cancelling requests...');
    cancelAllRequests();
    setIsTextSidebarOpen(false);
    
    // Clean up any blob URLs to prevent memory leaks
    if (podcastUrl && podcastUrl.startsWith('blob:')) {
      URL.revokeObjectURL(podcastUrl);
      setPodcastUrl(null);
    }
  }, [cancelAllRequests, podcastUrl]);

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      console.log('ReaderView unmounting, cleaning up...');
      cancelAllRequests();
      
      // Clean up any blob URLs
      if (podcastUrl && podcastUrl.startsWith('blob:')) {
        URL.revokeObjectURL(podcastUrl);
      }
    };
  }, [cancelAllRequests, podcastUrl]);

  // If no file is uploaded, redirect back to home
  if (!uploadedFile) {
    return (
      <div className="h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h3 className="text-lg font-medium text-foreground">No PDF Available</h3>
          <p className="text-muted-foreground">Please upload a PDF to get started</p>
          <button onClick={() => navigate('/')} className="text-primary hover:underline">
            Go back to upload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-background flex">
      <LibrarySidebar />
      
      <div className="flex-1 p-4 flex flex-col">
        <PDFViewer 
          uploadedFile={uploadedFile}
          onTextSelection={handleTextSelection}
          targetPage={targetPage}
          key={currentDocName}
        />
      </div>
      
      <RightSidebar />

      <TextSelectionSidebar
        isOpen={isTextSidebarOpen}
        onClose={handleSidebarClose} // Use the new handler with cancellation
        selectedText={selectedText}
        relatedSections={relatedSections}
        insights={insights}
        podcastUrl={podcastUrl}
        isLoadingRelated={isLoadingRelated}
        isLoadingInsights={isLoadingInsights}
        isLoadingPodcast={isLoadingPodcast}
        error={error}
        onSectionClick={handleSectionClick}
      />
    </div>
  );
};

export default ReaderView;