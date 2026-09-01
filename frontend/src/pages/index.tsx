import React from 'react';
import Head from 'next/head';
import TowerMap from '../components/TowerMap';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function Home() {
  return (
    <>
      <Head>
        <title>Cell Site Mapping & Analytics - Smart Communications</title>
        <meta name="description" content="Cell tower mapping and network analytics dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="flex flex-col h-screen">
        {/* Header */}
        <header className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg z-20">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">Cell Site Mapping & Analytics</h1>
                <p className="text-sm text-indigo-100 mt-1">
                  Smart Communications Network Infrastructure Visualization
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right text-sm">
                  <div className="font-medium">MCC: 515</div>
                  <div className="text-indigo-100">MNC: 03 (LTE/5G) | 05 (Legacy)</div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Map Container */}
        <div className="flex-1 relative">
          <TowerMap apiBaseUrl={API_BASE_URL} />
        </div>

        {/* Footer */}
        <footer className="bg-gray-800 text-white py-3 px-6 text-center text-sm z-20">
          <p>
            Cell Site Mapping System | Real-time Network Telemetry & Spatial Analytics |{' '}
            <span className="text-indigo-400">Manila, Philippines</span>
          </p>
        </footer>
      </main>
    </>
  );
}
