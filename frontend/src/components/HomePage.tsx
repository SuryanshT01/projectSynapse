import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Upload, FileText } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();
  const libraryInputRef = useRef<HTMLInputElement>(null);
  const readerInputRef = useRef<HTMLInputElement>(null);

  const handleLibraryUpload = () => {
    libraryInputRef.current?.click();
  };

  const handleReaderUpload = () => {
    readerInputRef.current?.click();
  };

  const handleLibraryFiles = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      // TODO: Send files to backend
      console.log('Library files selected:', files);
      // For now, just navigate to reader
      navigate('/reader');
    }
  };

  const handleReaderFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // TODO: Send file to backend
      console.log('Reader file selected:', file);
      navigate('/reader');
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8">
      <div className="max-w-4xl w-full text-center space-y-12">
        {/* Header */}
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-foreground tracking-tight">
            Document Insight Platform
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Upload, analyze, and extract insights from your PDF documents with AI-powered tools
          </p>
        </div>

        {/* Action Buttons */}
        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          <div 
            className="group cursor-pointer"
            onClick={handleLibraryUpload}
          >
            <div className="bg-card border-2 border-border rounded-2xl p-8 transition-all duration-200 hover:border-primary hover:shadow-lg hover:-translate-y-1">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 bg-adobe-red-light rounded-full flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-200">
                  <Upload className="w-8 h-8 text-primary group-hover:text-primary-foreground" />
                </div>
                <h2 className="text-2xl font-semibold text-foreground">
                  Add PDFs to Library
                </h2>
                <p className="text-muted-foreground text-center">
                  Upload multiple PDF documents to your library for future reference and analysis
                </p>
                <Button variant="outline" className="w-full max-w-xs">
                  Choose Files (up to 30)
                </Button>
              </div>
            </div>
          </div>

          <div 
            className="group cursor-pointer"
            onClick={handleReaderUpload}
          >
            <div className="bg-card border-2 border-border rounded-2xl p-8 transition-all duration-200 hover:border-primary hover:shadow-lg hover:-translate-y-1">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 bg-adobe-red-light rounded-full flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-200">
                  <FileText className="w-8 h-8 text-primary group-hover:text-primary-foreground" />
                </div>
                <h2 className="text-2xl font-semibold text-foreground">
                  Upload PDF to Read
                </h2>
                <p className="text-muted-foreground text-center">
                  Open a single PDF document immediately in the reader view for analysis
                </p>
                <Button className="w-full max-w-xs">
                  Choose File
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Hidden file inputs */}
        <input
          ref={libraryInputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleLibraryFiles}
          className="hidden"
        />
        <input
          ref={readerInputRef}
          type="file"
          accept=".pdf"
          onChange={handleReaderFile}
          className="hidden"
        />
      </div>
    </div>
  );
};

export default HomePage;