import { useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2, RotateCw } from 'lucide-react';

interface ImageViewerProps {
  src: string;
  alt?: string;
  title?: string;
}

export function ImageViewer({ src, alt, title }: ImageViewerProps) {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleReset = () => {
    setScale(1);
    setRotation(0);
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  return (
    <div className="w-full bg-gray-50 rounded-xl overflow-hidden">
      {title && (
        <div className="bg-white px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-medium text-black">{title}</h3>
        </div>
      )}

      {/* Image Container */}
      <div className="relative bg-gray-900 flex items-center justify-center min-h-[400px] max-h-[70vh] overflow-auto">
        <img
          src={src}
          alt={alt || 'Evidence image'}
          className="max-w-full max-h-[70vh] object-contain transition-transform duration-300"
          style={{
            transform: `scale(${scale}) rotate(${rotation}deg)`,
          }}
        />
      </div>

      {/* Controls */}
      <div className="bg-white px-4 py-3 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              disabled={scale <= 0.5}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Zoom out"
            >
              <ZoomOut className="w-5 h-5 text-gray-700" strokeWidth={2} />
            </button>

            <span className="text-sm font-medium text-gray-900 min-w-[60px] text-center">
              {Math.round(scale * 100)}%
            </span>

            <button
              onClick={handleZoomIn}
              disabled={scale >= 3}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Zoom in"
            >
              <ZoomIn className="w-5 h-5 text-gray-700" strokeWidth={2} />
            </button>

            <div className="w-px h-6 bg-gray-300 mx-2" />

            <button
              onClick={handleRotate}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Rotate 90°"
            >
              <RotateCw className="w-5 h-5 text-gray-700" strokeWidth={2} />
            </button>

            <button
              onClick={handleReset}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Reset view"
            >
              <Maximize2 className="w-5 h-5 text-gray-700" strokeWidth={2} />
            </button>
          </div>

          <div className="text-xs text-gray-500">
            Use scroll to zoom • Click and drag to pan
          </div>
        </div>
      </div>
    </div>
  );
}
