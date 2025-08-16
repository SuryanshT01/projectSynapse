// src/pages/ReaderView.tsx
import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import LibrarySidebar from '@/components/LibrarySidebar';
import PDFViewer from '@/components/PDFViewer';
import RightSidebar from '@/components/RightSidebar';
import TextSelectionSidebar from '@/components/TextSelectionSidebar';
import { RelatedSection, Insights } from '@/types/analysis'; // <-- Import new types

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

  useEffect(() => {
    if (location.state?.uploadedFile) {
      setUploadedFile(location.state.uploadedFile);
    }
  }, [location.state]);

  const startAnalysisFlow = useCallback(async (text: string) => {
    // Reset all states for a new analysis
    setIsTextSidebarOpen(true);
    setRelatedSections([]);
    setInsights(null);
    setPodcastUrl(null);
    setError(null);
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    try {
      // Step 1: Fetch Related Sections
      setIsLoadingRelated(true);
      const sectionsResponse = await fetch(`${apiUrl}/related-sections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: text }),
      });
      if (!sectionsResponse.ok) throw new Error('Failed to fetch related sections.');
      const sections: RelatedSection[] = await sectionsResponse.json();
      setRelatedSections(sections);
      setIsLoadingRelated(false);
      
      const relatedSnippets = sections.map(s => s.snippet);

      // Step 2: Fetch Insights (depends on related sections)
      setIsLoadingInsights(true);
      const insightsResponse = await fetch(`${apiUrl}/insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: text, related_snippets: relatedSnippets }),
      });
      if (!insightsResponse.ok) throw new Error('Failed to generate insights.');
      const insightData: Insights = await insightsResponse.json();
      setInsights(insightData);
      setIsLoadingInsights(false);

      // Step 3: Fetch Podcast (also depends on related sections)
      setIsLoadingPodcast(true);
      const podcastResponse = await fetch(`${apiUrl}/podcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: text, related_snippets: relatedSnippets }),
      });
      if (!podcastResponse.ok) throw new Error('Failed to generate podcast audio.');
      const audioBlob = await podcastResponse.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      setPodcastUrl(audioUrl);
      setIsLoadingPodcast(false);

    } catch (err: any) {
      console.error("Analysis flow failed:", err);
      setError(err.message || 'An unknown error occurred during analysis.');
      // Stop all loading indicators on error
      setIsLoadingRelated(false);
      setIsLoadingInsights(false);
      setIsLoadingPodcast(false);
    }
  }, []);

  const handleTextSelection = useCallback((text: string) => {
    // This is the trigger for the entire journey flow
    if (text && text.length > 10) { // Add a minimum length to avoid accidental triggers
      setSelectedText(text);
      startAnalysisFlow(text);
    }
  }, [startAnalysisFlow]);

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
        />
      </div>
      
      <RightSidebar />

      <TextSelectionSidebar
        isOpen={isTextSidebarOpen}
        onClose={() => setIsTextSidebarOpen(false)}
        selectedText={selectedText}
        // Pass all the new data and states to the sidebar
        relatedSections={relatedSections}
        insights={insights}
        podcastUrl={podcastUrl}
        isLoadingRelated={isLoadingRelated}
        isLoadingInsights={isLoadingInsights}
        isLoadingPodcast={isLoadingPodcast}
        error={error}
      />
    </div>
  );
};

export default ReaderView;