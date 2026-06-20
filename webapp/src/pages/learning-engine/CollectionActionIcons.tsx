type IconProps = {
  className?: string;
};

export const BookmarkIcon = ({ className }: IconProps) => (
  <svg aria-hidden="true" className={className} fill="none" focusable="false" viewBox="0 0 24 24">
    <path
      d="M7 4.75h10a1.25 1.25 0 0 1 1.25 1.25v13.25L12 15.75l-6.25 3.5V6A1.25 1.25 0 0 1 7 4.75Z"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);

export const HeartIcon = ({ className }: IconProps) => (
  <svg aria-hidden="true" className={className} fill="none" focusable="false" viewBox="0 0 24 24">
    <path
      d="M12 19.25s-7.25-4.4-7.25-9.25A3.75 3.75 0 0 1 11.4 7.6L12 8.4l.6-.8A3.75 3.75 0 0 1 19.25 10c0 4.85-7.25 9.25-7.25 9.25Z"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);

export const PencilIcon = ({ className }: IconProps) => (
  <svg aria-hidden="true" className={className} fill="none" focusable="false" viewBox="0 0 24 24">
    <path
      d="m5.25 18.75 3.5-.75 9.35-9.35a2.05 2.05 0 0 0-2.9-2.9L5.85 15.1l-.6 3.65ZM13.75 7.2l3.05 3.05"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);

export const PauseIcon = ({ className }: IconProps) => (
  <svg aria-hidden="true" className={className} fill="none" focusable="false" viewBox="0 0 24 24">
    <path
      d="M9.25 7.25v9.5M14.75 7.25v9.5"
      stroke="currentColor"
      strokeLinecap="round"
      strokeWidth="1.9"
    />
  </svg>
);

export const PlayIcon = ({ className }: IconProps) => (
  <svg aria-hidden="true" className={className} fill="none" focusable="false" viewBox="0 0 24 24">
    <path
      d="M8.75 6.75v10.5l8-5.25-8-5.25Z"
      stroke="currentColor"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);

export const TrashIcon = ({ className }: IconProps) => (
  <svg aria-hidden="true" className={className} fill="none" focusable="false" viewBox="0 0 24 24">
    <path
      d="M5 7.25h14M9.75 7.25V5.5h4.5v1.75m-7 0 .75 11.25a1.25 1.25 0 0 0 1.25 1.15h5.5A1.25 1.25 0 0 0 16 18.5l.75-11.25M10.25 10.5v5.75M13.75 10.5v5.75"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);
