import React from 'react';
import BookFinderCard from './BookFinderCard';
import HNCard from './HNCard';
import HolidaysCard from './HolidaysCard';
import WeatherCard from './WeatherCard';

const PublicApisPanel: React.FC = () => {
    return (
        <div className="col-span-1 md:col-span-2 lg:col-span-3">
            <h2 className="text-lg font-semibold mb-2 dark:text-white">Public APIs</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <WeatherCard />
                <HNCard />
                <BookFinderCard />
                <HolidaysCard />
            </div>
        </div>
    );
};

export default PublicApisPanel;
// single export above
