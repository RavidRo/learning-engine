type ToastProps = {
  message: string;
  visible: boolean;
};

export const Toast = ({ message, visible }: ToastProps) => (
  <div className={`toast ${visible ? "show" : ""}`} role="status" aria-live="polite">
    {message}
  </div>
);
