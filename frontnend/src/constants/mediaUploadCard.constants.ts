import type { ComponentType, SVGAttributes } from 'react';

type IconComponent = ComponentType<SVGAttributes<SVGElement> & { strokeWidth?: number }>;

export type MediaFileType = 'video' | 'image' | 'audio' | 'document';
export type UploadStatus = 'uploading' | 'completed' | 'error';

/**
 * Maps a media file type to the corresponding Lucide icon component name.
 * The actual icon is looked up at runtime to avoid circular imports.
 */
export const FILE_TYPE_ICON_MAP: Record<MediaFileType, string> = {
  video: 'Video',
  image: 'ImageIcon',
  audio: 'Music',
  document: 'FileText',
};

/**
 * Maps upload status to the Tailwind text-colour class for the file icon.
 */
export const UPLOAD_STATUS_ICON_COLOR: Record<UploadStatus, string> = {
  completed: 'text-black',
  error: 'text-red-500',
  uploading: 'text-gray-600',
};
