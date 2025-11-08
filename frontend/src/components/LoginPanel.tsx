import './LoginPanel.css';

interface LoginPanelProps {
  title: string;
  buttonText?: string;
}

export default function LoginPanel({ title, buttonText = "log in" }: LoginPanelProps) {
  return (
    <div className="glass-card login-panel">
      <div className="glass-filter"></div>
      <div className="glass-overlay"></div>
      <div className="glass-specular"></div>
      <div className="glass-content">
        <h2 className="login-panel-title">{title}</h2>

        <div className="login-panel-video-container glass-card">
          <div className="glass-filter"></div>
          <div className="glass-overlay"></div>
          <div className="glass-specular"></div>
          {/* Video placeholder */}
        </div>

        <div className="login-panel-terminal glass-card">
          <div className="glass-filter"></div>
          <div className="glass-overlay"></div>
          <div className="glass-specular"></div>
          {/* Terminal content */}
        </div>

        <button className="login-panel-button">{buttonText}</button>
      </div>
    </div>
  );
}
