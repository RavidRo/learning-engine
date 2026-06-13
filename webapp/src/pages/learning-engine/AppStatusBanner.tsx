type AppStatusBannerProps = {
  isOffline: boolean;
  onRefreshUpdate: () => void;
  updateAvailable: boolean;
};

export const AppStatusBanner = ({
  isOffline,
  onRefreshUpdate,
  updateAvailable,
}: AppStatusBannerProps) => {
  if (isOffline) {
    return (
      <div className="app-status-banner offline" role="status">
        <span>Offline. Live updates and saving need a connection.</span>
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
