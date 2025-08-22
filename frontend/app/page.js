import ChatContainer from './components/ChatContainer';
import Image from 'next/image';

export default function Home() {
  return (
    <div className="page">
      <div className="red-bar">
      <Image
          src="/assets/info_icon.png"
          alt="Icon"
          width={40}
          height={40}
          className="icon"
        />
      </div>
      <header>
        <Image
        src="/assets/pbots_logo.png"          
        alt="PBOTS Logo"
        width={80}
        height={80}
        />
        <h1>PBotS</h1>
        <p>Zadaj pytanie!</p>
      </header>
      <ChatContainer />
    </div>
  );
}
