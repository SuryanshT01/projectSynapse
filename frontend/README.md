# Project Synapse Frontend

## Adobe PDF Embed API Setup

This project integrates Adobe PDF Embed API for PDF viewing and text selection capabilities.

### Prerequisites

1. **Adobe Developer Account**: You need an Adobe Developer account to get a Client ID
2. **Node.js**: Version 18 or higher
3. **Package Manager**: npm, yarn, or bun

### Quick Setup

1. **Run the setup script**:
   ```bash
   chmod +x setup-env.sh && ./setup-env.sh
   ```

2. **Get Adobe Client ID**:
   - Go to [Adobe Developer Console](https://www.adobe.com/go/dcsdks_credentials)
   - Sign in with your Adobe account
   - Create a new project or use an existing one
   - Add the "PDF Embed API" service
   - Copy your Client ID

3. **Configure Environment Variables**:
   ```bash
   # Edit the .env file created by setup script
   nano .env
   
   # Replace 'your-adobe-client-id-here' with your actual Client ID
   VITE_ADOBE_CLIENT_ID=abc123def456ghi789
   ```

4. **Install Dependencies**:
   ```bash
   npm install
   # or
   yarn install
   # or
   bun install
   ```

5. **Start Development Server**:
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   bun dev
   ```

### Manual Setup

If you prefer to set up manually:

1. **Create `.env` file**:
   ```bash
   # Create .env file in the frontend directory
   echo "VITE_ADOBE_CLIENT_ID=your-actual-client-id-here" > .env
   echo "VITE_API_URL=http://localhost:8000" >> .env
   ```

2. **Follow steps 2-5 from Quick Setup above**

### Features

- **PDF Upload**: Upload PDFs from the home page
- **PDF Viewer**: View PDFs using Adobe PDF Embed API
- **Text Selection**: Select text in PDFs to trigger analysis
- **Zoom Controls**: Zoom in/out and reset zoom level
- **Responsive Design**: Works on desktop and mobile devices

### File Structure

```
frontend/
├── .env
├── README.md
├── bun.lockb
├── components.json
├── dist/
├── eslint.config.js
├── index.html
├── node_modules/
├── package-lock.json
├── package.json
├── postcss.config.js
├── public/
│   ├── placeholder.svg
│   └── robots.txt
├── src/
│   ├── App.css
│   ├── App.tsx
│   ├── components/
│   │   ├── AdobePDFViewer.tsx
│   │   ├── AdobeTest.tsx
│   │   ├── HomePage.tsx
│   │   ├── LibrarySidebar.tsx
│   │   ├── ModalPrompt.tsx
│   │   ├── PDFViewer.tsx
│   │   ├── RightSidebar.tsx
│   │   ├── TextSelectionSidebar.tsx
│   │   └── ui/
│   ├── hooks/
│   │   ├── use-mobile.tsx
│   │   ├── use-toast.ts
│   │   └── useAdobeViewSDK.ts
│   ├── index.css
│   ├── lib/
│   │   └── utils.ts
│   ├── main.tsx
│   ├── pages/
│   │   ├── HistoryPage.tsx
│   │   ├── Index.tsx
│   │   ├── NotFound.tsx
│   │   └── ReaderView.tsx
│   ├── types/
│   │   ├── adobe.d.ts
│   │   └── analysis.ts
│   └── vite-env.d.ts
├── tailwind.config.ts
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

### Troubleshooting

**Having issues?** Check our comprehensive [Troubleshooting Guide](./TROUBLESHOOTING.md) for common problems and solutions.

**Common Issues:**
- "Adobe PDF Embed API Client ID not configured" → Set `VITE_ADOBE_CLIENT_ID` in `.env`
- PDF not loading → Check Adobe Client ID and internet connection
- Text selection not working → Verify Adobe viewer is fully loaded

### API Integration

The Adobe PDF Embed API provides:
- PDF rendering and display
- Text selection events
- Zoom and navigation controls
- Responsive design
- Cross-platform compatibility

### Development Notes

- The Adobe script is loaded dynamically when the component mounts
- Text selection events are captured and passed to parent components
- File uploads are handled through React Router state
- The viewer supports both uploaded files and library files
- 30-second timeout for PDF loading with user feedback

### Testing

1. **Upload a PDF**: Go to home page → "Upload PDF to Read"
2. **View PDF**: Adobe viewer should load the PDF
3. **Select Text**: Click and drag to select text in PDF
4. **Check Console**: Look for Adobe API events and debug messages

### Support

- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Adobe Documentation**: [Adobe Developer Console](https://www.adobe.com/go/dcsdks_credentials)
- **Project Issues**: Check the main project repository
