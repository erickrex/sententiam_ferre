import React, { useState } from 'react';
import { exportAPI } from '../services/api';
import './ExportPanel.css';

/**
 * ExportPanel component provides download buttons for character images and parameters.
 * 
 * Requirements: 9.1, 9.2
 * - Download Image button for the image file
 * - Export Parameters (JSON) button for the JSON schema
 */
function ExportPanel({ item, onError }) {
  const [downloadingImage, setDownloadingImage] = useState(false);
  const [downloadingJson, setDownloadingJson] = useState(false);

  const attributes = item?.attributes || {};
  const hasImage = !!attributes.image_url;
  const description = attributes.description || item?.label || 'character';
  const version = attributes.version || 1;

  // Helper to trigger file download from blob
  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  // Generate filename from description
  const generateFilename = (extension) => {
    const sanitized = description
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .replace(/\s+/g, '_')
      .substring(0, 50);
    return `${sanitized}_v${version}.${extension}`;
  };

  const handleDownloadImage = async () => {
    if (!item?.id || downloadingImage) return;

    setDownloadingImage(true);
    try {
      const response = await exportAPI.downloadImage(item.id);
      const filename = generateFilename('png');
      downloadBlob(response.data, filename);
    } catch (err) {
      const message = err.message || 'Failed to download image';
      onError?.(message);
    } finally {
      setDownloadingImage(false);
    }
  };

  const handleExportParameters = async () => {
    if (!item?.id || downloadingJson) return;

    setDownloadingJson(true);
    try {
      const response = await exportAPI.exportParameters(item.id);
      const filename = generateFilename('json');
      downloadBlob(response.data, filename);
    } catch (err) {
      const message = err.message || 'Failed to export parameters';
      onError?.(message);
    } finally {
      setDownloadingJson(false);
    }
  };

  if (!item) {
    return null;
  }

  return (
    <div className="export-panel">
      <h4 className="export-panel-title">Export</h4>
      <div className="export-panel-buttons">
        <button
          className="export-btn image-btn"
          onClick={handleDownloadImage}
          disabled={!hasImage || downloadingImage}
          title={hasImage ? 'Download character image' : 'No image available'}
        >
          {downloadingImage ? (
            <>
              <span className="btn-spinner"></span>
              Downloading...
            </>
          ) : (
            <>
              <span className="btn-icon">📥</span>
              Download Image
            </>
          )}
        </button>
        
        <button
          className="export-btn json-btn"
          onClick={handleExportParameters}
          disabled={downloadingJson}
          title="Export generation parameters as JSON"
        >
          {downloadingJson ? (
            <>
              <span className="btn-spinner"></span>
              Exporting...
            </>
          ) : (
            <>
              <span className="btn-icon">📄</span>
              Export Parameters
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default ExportPanel;
