// Facebook SDK TypeScript declarations
interface Window {
  FB?: {
    init: (params: {
      appId: string;
      cookie?: boolean;
      autoLogAppEvents?: boolean;
      xfbml?: boolean;
      version: string;
    }) => void;
    login: (
      callback: (response: any) => void,
      options?: {
        config_id?: string;
        response_type?: string;
        override_default_response_type?: boolean;
        extras?: {
          setup?: Record<string, any>;
          featureType?: string;
          sessionInfoVersion?: number | string;
          [key: string]: any;
        };
      }
    ) => void;
  };
}
