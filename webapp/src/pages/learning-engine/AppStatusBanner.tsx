type AppStatusBannerProps = {
  isConnectionUnavailable: boolean;
  onRefreshUpdate: () => void;
  updateAvailable: boolean;
};

export const AppStatusBanner = ({
  isConnectionUnavailable,
  onRefreshUpdate,
  updateAvailable,
}: AppStatusBannerProps) => {
  if (isConnectionUnavailable) {
    return (
      <div className="app-status-banner connection-unavailable" role="status">
        <span>Connection unavailable. Live updates and saving need the service.</span>
      </div>
    );
  }

  if (updateAvailable) {
    return (
      <div className="app-status-banner update" role="status">
        <span>Update available.</span>
        <button className="button compact ghost" type="button" onClick={onRefreshUpdate}>
          Refresh
        </button>
      </div>
    );
  }

  return null;
};
