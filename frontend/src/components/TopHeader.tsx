import { FaGithub } from 'react-icons/fa';
import { SiDevpost } from 'react-icons/si';
import './TopHeader.css';

const TopHeader = () => {
  return (
    <div className="top-header-container">
      <a
        href="https://github.com"
        target="_blank"
        rel="noopener noreferrer"
        className="header-icon header-icon-left"
      >
        <FaGithub />
      </a>

      <div className="mlh-logo">
        <img src="/mlh.png" alt="MLH" />
      </div>

      <a
        href="https://devpost.com"
        target="_blank"
        rel="noopener noreferrer"
        className="header-icon header-icon-right"
      >
        <SiDevpost />
      </a>
    </div>
  );
};

export default TopHeader;
