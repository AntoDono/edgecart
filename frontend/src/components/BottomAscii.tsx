// @ts-nocheck
import { useEffect, useState } from 'react';
import './BottomAscii.css';

const BottomAscii = () => {
  const centerArt = `          .          .         .           .    ..     .    .          .    .  .  .    .     .
        .          .. .          .     .         .                     ..             ..          .    . .   ..                  .
           .       .                .     .                         .   ..:::::::..              .   ..         .        .           .
      .                        .    ..  .      ..  .                 .:++-+*****-. .          ..  .            . . .          .   . .
          .  . .. .       ..           .      .         .             ..=#+=**+=*+.    . .    .    .   .      .                              . ..
 .                          .         .         .. .                   .:*#+==+*#-.                                        .                 .
             .       . .   .. .          .                .  .    .     .=*+-:::..        .                      .        . ..     . .      . .
  .  ..  .     .  . .... .   .    .                  .         .  .    . .-=---=:.  . .              .   .                                       .
    .    ..        .. .  .  . .       .      .                . .      . .:-. :-..  . .    ..   .     .         .           . .        .
        .       .       .     .            .   .  . ..          . ..    . .    .             .   .   .    . ..              .   . . ... .    .`;
  const randomChars = '.:-=+*#@%&';

  const generateRandomAscii = (width: number, height: number) => {
    let result = '';
    const cornerRadius = 3; // How many rows/cols to round

    for (let i = 0; i < height; i++) {
      for (let j = 0; j < width; j++) {
        // Calculate distance from corners for rounding effect
        const distFromTopLeft = Math.sqrt(Math.pow(Math.max(0, cornerRadius - i), 2) + Math.pow(Math.max(0, cornerRadius - j), 2));
        const distFromTopRight = Math.sqrt(Math.pow(Math.max(0, cornerRadius - i), 2) + Math.pow(Math.max(0, cornerRadius - (width - 1 - j)), 2));
        const distFromBottomLeft = Math.sqrt(Math.pow(Math.max(0, cornerRadius - (height - 1 - i)), 2) + Math.pow(Math.max(0, cornerRadius - j), 2));
        const distFromBottomRight = Math.sqrt(Math.pow(Math.max(0, cornerRadius - (height - 1 - i)), 2) + Math.pow(Math.max(0, cornerRadius - (width - 1 - j)), 2));

        // If we're in a corner that should be rounded, add space
        const inCorner = distFromTopLeft > cornerRadius || distFromTopRight > cornerRadius ||
                        distFromBottomLeft > cornerRadius || distFromBottomRight > cornerRadius;

        if (inCorner) {
          result += ' ';
        } else {
          result += randomChars[Math.floor(Math.random() * randomChars.length)];
        }
      }
      if (i < height - 1) result += '\n';
    }
    return result;
  };

  const [leftAscii, setLeftAscii] = useState('');
  const [rightAscii, setRightAscii] = useState('');

  useEffect(() => {
    // Generate random ASCII for left and right sides
    const artLines = centerArt.split('\n');
    const artHeight = artLines.length;

    setLeftAscii(generateRandomAscii(50, artHeight));
    setRightAscii(generateRandomAscii(50, artHeight));

    // Regenerate every 3 seconds for a dynamic effect
    const interval = setInterval(() => {
      setLeftAscii(generateRandomAscii(50, artHeight));
      setRightAscii(generateRandomAscii(50, artHeight));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bottom-ascii-container">
      <div className="ascii-content">
        <pre className="ascii-left">{leftAscii}</pre>
        <pre className="ascii-center">{centerArt}</pre>
        <pre className="ascii-right">{rightAscii}</pre>
      </div>
    </div>
  );
};

export default BottomAscii;
