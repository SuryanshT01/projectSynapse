// src/types/analysis.ts

export interface RelatedSection {
    doc_name: string;
    section_title: string;
    page: number;
    snippet: string;
  }
  
  // Assuming insights will be a JSON object with various keys
  export interface Insights {
    [key: string]: any;
  }