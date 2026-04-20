import { createContext, useContext, type ReactNode } from 'react';
import type { ApiAdapter } from '../adapters/types';
import { createMockAdapter } from '../adapters/mock-adapter';

const ApiContext = createContext<ApiAdapter>(createMockAdapter());

export function useApi(): ApiAdapter {
  return useContext(ApiContext);
}

interface ApiProviderProps {
  adapter: ApiAdapter;
  children: ReactNode;
}

export function ApiProvider({ adapter, children }: ApiProviderProps) {
  return <ApiContext.Provider value={adapter}>{children}</ApiContext.Provider>;
}
