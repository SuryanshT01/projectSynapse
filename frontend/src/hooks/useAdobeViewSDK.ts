// src/hooks/useAdobeViewSDK.ts
import { useState, useEffect } from 'react';

type SdkStatus = 'LOADING' | 'READY' | 'ERROR';

interface AdobeSDKState {
  status: SdkStatus;
  error: Error | null;
}

// Create a singleton promise to ensure the script loading and initialization
// logic runs only once across the entire application.
let sdkReadyPromise: Promise<void> | null = null;

/**
 * A custom React hook to manage the lifecycle of the Adobe PDF Embed API SDK.
 * It handles loading the external script and listening for the 'adobe_dc_view_sdk.ready' event.
 * This ensures the SDK is loaded and ready before any component attempts to use it.
 *
 * @returns {AdobeSDKState} An object containing the current status of the SDK ('LOADING', 'READY', 'ERROR') and any potential error.
 */
export const useAdobeViewSDK = (): AdobeSDKState => {
  const [sdkState, setSdkState] = useState<AdobeSDKState>({
    status: window.AdobeDC ? 'READY' : 'LOADING',
    error: null,
  });

  useEffect(() => {
    // If the SDK is already ready (e.g., from a previous mount), do nothing.
    if (window.AdobeDC) {
      setSdkState({ status: 'READY', error: null });
      return;
    }

    // If the SDK is already being loaded by another component, just wait for the promise to resolve.
    if (sdkReadyPromise) {
      sdkReadyPromise
       .then(() => setSdkState({ status: 'READY', error: null }))
       .catch((error) => setSdkState({ status: 'ERROR', error }));
      return;
    }

    // This is the first component to request the SDK, so we initiate the loading process.
    sdkReadyPromise = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://acrobatservices.adobe.com/view-sdk/viewer.js';
      script.async = true;

      const handleReady = () => {
        console.log('Adobe View SDK is ready.');
        resolve();
        // Clean up the event listener once the SDK is ready.
        document.removeEventListener('adobe_dc_view_sdk.ready', handleReady);
      };

      script.onload = () => {
        // The script has loaded, now we must wait for the SDK's internal ready event.
        document.addEventListener('adobe_dc_view_sdk.ready', handleReady);
      };

      script.onerror = (error) => {
        console.error('Failed to load the Adobe View SDK script.', error);
        const loadError = new Error('Failed to load Adobe PDF Embed API script.');
        reject(loadError);
      };

      document.head.appendChild(script);
    });

    // Update component state based on the promise resolution.
    sdkReadyPromise
     .then(() => setSdkState({ status: 'READY', error: null }))
     .catch((error) => setSdkState({ status: 'ERROR', error }));

  }, []); // Empty dependency array ensures this effect runs only once per component mount.

  return sdkState;
};