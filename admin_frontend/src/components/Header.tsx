interface HeaderProps {
  onReset: () => void;
}

export const Header = ({ onReset }: HeaderProps) => {
  return (
    <div className="header">
      <h1>
        <span>🏢</span>
        Travel Booking Admin Panel
      </h1>
      <div className="header-actions">
        <button className="btn btn-secondary" onClick={onReset}>
          Clear Chat
        </button>
      </div>
    </div>
  );
};
