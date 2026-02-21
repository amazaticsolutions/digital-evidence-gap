/** Supported file size display units, ordered from smallest to largest. */
export const FILE_SIZE_UNITS = ['Bytes', 'KB', 'MB', 'GB'] as const;

/** Accepted MIME types / extensions for the evidence file upload input. */
export const ACCEPTED_FILE_TYPES = 'video/*,image/*,audio/*,.pdf,.doc,.docx';

/** Interval in milliseconds between simulated upload progress ticks. */
export const UPLOAD_SIMULATION_INTERVAL_MS = 500;

/** Maximum random increment per tick during simulated upload (0–15%). */
export const UPLOAD_SIMULATION_MAX_INCREMENT = 15;
