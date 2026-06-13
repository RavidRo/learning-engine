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
