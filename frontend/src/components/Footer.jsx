import React from 'react';

const Footer = () => {
  const tiktokUrl = import.meta.env.VITE_TIKTOK_URL || 'https://www.tiktok.com';
  const instagramUrl = import.meta.env.VITE_INSTAGRAM_URL || 'https://www.instagram.com';
  const blueskyUrl = import.meta.env.VITE_BLUESKY_URL || 'https://bsky.app';
  const xUrl = import.meta.env.VITE_X_URL || 'https://x.com';

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-center space-x-6">
          <a href={tiktokUrl} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-500">
            <span className="sr-only">TikTok</span>
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0 1 15.54 3h-3.09v12.4a2.592 2.592 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3s-1.88.09-3.24-1.48z" />
            </svg>
          </a>

          <a href={instagramUrl} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-500">
            <span className="sr-only">Instagram</span>
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path fillRule="evenodd" d="M12.315 2c2.43 0 2.784.013 3.808.06 1.064.049 1.791.218 2.427.465a4.902 4.902 0 011.772 1.153 4.902 4.902 0 011.153 1.772c.247.636.416 1.363.465 2.427.048 1.067.06 1.407.06 4.123v.08c0 2.643-.012 2.987-.06 4.043-.049 1.064-.218 1.791-.465 2.427a4.902 4.902 0 01-1.153 1.772 4.902 4.902 0 01-1.772 1.153c-.636.247-1.363.416-2.427.465-1.067.048-1.407.06-4.123.06h-.08c-2.643 0-2.987-.012-4.043-.06-1.064-.049-1.791-.218-2.427-.465a4.902 4.902 0 01-1.772-1.153 4.902 4.902 0 01-1.153-1.772c-.247-.636-.416-1.363-.465-2.427-.047-1.024-.06-1.379-.06-3.808v-.63c0-2.43.013-2.784.06-3.808.049-1.064.218-1.791.465-2.427a4.902 4.902 0 011.153-1.772 4.902 4.902 0 011.772-1.153c.636-.247 1.363-.416 2.427-.465C9.673 2.013 10.03 2 12.48 2h-.165zm-2.386 5.8c-2.03 0-3.674 1.644-3.674 3.674 0 2.03 1.644 3.674 3.674 3.674 2.03 0 3.674-1.644 3.674-3.674 0-2.03-1.644-3.674-3.674-3.674zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" clipRule="evenodd" />
            </svg>
          </a>

          <a href={xUrl} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-500">
            <span className="sr-only">X (Twitter)</span>
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
          </a>

          <a href={blueskyUrl} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-500">
            <span className="sr-only">Bluesky</span>
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565-.131 2.032-.025 3.023.048 3.28c.112.402 1.341 5.952 2.698 8.452.859 1.571 2.493 3.128 5.339 3.128-2.679 1.543-5.211 4.713-3.193 8.095.663 1.112 2.68 2.257 5.74 1.325 2.896-.885 1.367-5.518 1.367-5.518s-1.528 4.633 1.368 5.518c3.06.932 5.077-.213 5.74-1.325 2.017-3.382-.514-6.552-3.193-8.095 2.846 0 4.48-1.557 5.339-3.128 1.357-2.5 2.586-8.05 2.698-8.452.073-.257.179-1.248-.854-1.715-.66-.299-1.664-.621-4.3 1.24C16.046 4.748 13.087 8.686 12 10.8z" />
            </svg>
          </a>
        </div>
        <p className="mt-8 text-center text-base text-gray-400">
          &copy; {new Date().getFullYear()} CompInput. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export default Footer;