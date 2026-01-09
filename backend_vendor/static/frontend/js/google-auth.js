// Google OAuth Integration for NexaMart
class GoogleAuth {
    constructor() {
        // Check if Google auth is disabled (demo mode)
        if (window.DISABLE_GOOGLE_AUTH) {
            console.log('🚫 Google Auth disabled (demo mode)');
            this.isDisabled = true;
            return;
        }

        this.isDisabled = false;
        this.clientId = '735742648650-4fnealrih29hufng0ss2b185iq0o2rf0.apps.googleusercontent.com';
        this.isInitialized = false;
        this.gapi = null;
        this.redirectUri = window.location.origin + '/login/'; // Redirect back to login page (with trailing slash to match Django URL)
        // Use redirect flow for localhost (more reliable) - popup flow has origin issues
        this.useRedirect = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

        // Debug: log current origin
        console.log('🔧 Google Auth Config:');
        console.log('   - Origin:', window.location.origin);
        console.log('   - Client ID:', this.clientId);
        console.log('   - Redirect URI:', this.redirectUri);
        console.log('   - Using redirect flow:', this.useRedirect);
    }

    async init() {
        // Skip if disabled
        if (this.isDisabled) {
            return;
        }

        try {
            // Load Google API script
            await this.loadGoogleAPI();
            
            // Initialize Google Auth
            await this.initializeGoogleAuth();
            
            this.isInitialized = true;
            console.log('Google Auth initialized successfully');
        } catch (error) {
            console.error('Google Auth initialization failed:', error);
        }
    }

    loadGoogleAPI() {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (window.google && window.google.accounts) {
                resolve(window.google);
                return;
            }

            // Load new Google Identity Services
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.onload = () => {
                this.google = window.google;
                resolve(window.google);
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async initializeGoogleAuth() {
        // Initialize Google Identity Services
        window.google.accounts.id.initialize({
            client_id: this.clientId,
            callback: this.handleCredentialResponse.bind(this),
            auto_select: false,
            cancel_on_tap_outside: true,
            use_fedcm_for_prompt: false  // Disable FedCM to avoid CORS issues
        });
    }

    handleCredentialResponse(response) {
        // This will be called when user signs in
        this.credentialResponse = response;
    }

    async signIn() {
        // Block if disabled (demo mode)
        if (this.isDisabled) {
            console.log('🚫 Google Sign-in blocked (demo mode)');
            alert('Sign-in is disabled in demo mode. This is just a preview!');
            return { success: false, disabled: true };
        }

        return new Promise((resolve, reject) => {
            try {
                // For localhost, use redirect flow (more reliable, avoids origin issues)
                if (this.useRedirect) {
                    console.log('🔵 Using redirect-based OAuth flow (recommended for localhost)');
                    this.performRedirectSignIn();
                    // Return pending since we're redirecting
                    resolve({
                        success: false,
                        redirecting: true,
                        message: 'Redirecting to Google...'
                    });
                    return;
                }

                if (!this.isInitialized) {
                    this.init().then(() => {
                        this.performSignIn(resolve, reject);
                    });
                } else {
                    this.performSignIn(resolve, reject);
                }
            } catch (error) {
                console.error('Google sign-in failed:', error);
                resolve({
                    success: false,
                    error: error.message || 'Google sign-in failed'
                });
            }
        });
    }

    // New redirect-based sign-in method (no popup needed!)
    performRedirectSignIn() {
        console.log('🔵 Starting redirect-based Google sign-in...');
        console.log('✅ No popup blocker issues - using full page redirect!');
        console.log('📋 Redirect URI:', this.redirectUri);
        console.log('📋 Make sure this EXACT URI is in Google Cloud Console "Authorized redirect URIs"');

        // Save current state before redirect
        sessionStorage.setItem('google_auth_initiated', 'true');
        sessionStorage.setItem('auth_return_url', window.location.pathname);

        // Build OAuth URL manually for redirect flow
        const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
        authUrl.searchParams.set('client_id', this.clientId);
        authUrl.searchParams.set('redirect_uri', this.redirectUri);
        authUrl.searchParams.set('response_type', 'id_token token');
        authUrl.searchParams.set('scope', 'openid profile email');
        authUrl.searchParams.set('nonce', this.generateNonce());
        authUrl.searchParams.set('prompt', 'select_account');

        console.log('🔵 OAuth URL:', authUrl.toString());
        console.log('🔵 Redirecting to Google OAuth...');

        // Redirect to Google OAuth
        window.location.href = authUrl.toString();
    }

    // Generate a random nonce for security
    generateNonce() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    // Check if we're returning from Google OAuth redirect
    handleRedirectCallback() {
        console.log('🔍 Checking for OAuth redirect callback...');
        console.log('   - Current URL:', window.location.href);
        console.log('   - Hash:', window.location.hash ? 'present' : 'none');

        // Check if we initiated Google auth
        const authInitiated = sessionStorage.getItem('google_auth_initiated');

        if (!authInitiated) {
            console.log('ℹ️ No auth redirect detected (no session marker)');
            return null;
        }

        // Check for OAuth response in URL hash
        const hash = window.location.hash;
        if (!hash) {
            console.log('ℹ️ Auth was initiated but no hash in URL yet');
            return null;
        }

        console.log('🔵 Processing OAuth callback from URL hash...');
        
        // Parse hash parameters
        const params = new URLSearchParams(hash.substring(1));
        const idToken = params.get('id_token');
        const accessToken = params.get('access_token');
        
        if (idToken) {
            console.log('✅ ID token found in redirect!');
            
            // Clear auth state
            sessionStorage.removeItem('google_auth_initiated');
            const returnUrl = sessionStorage.getItem('auth_return_url') || '/';
            sessionStorage.removeItem('auth_return_url');
            
            // Parse the JWT token
            try {
                const payload = this.parseJwt(idToken);
                console.log('✅ User info decoded from token:', payload);
                
                // Clean up URL (remove hash)
                history.replaceState({}, document.title, returnUrl);
                
                return {
                    success: true,
                    user: {
                        id: payload.sub,
                        name: payload.name,
                        email: payload.email,
                        picture: payload.picture,
                        givenName: payload.given_name,
                        familyName: payload.family_name
                    },
                    idToken: idToken,
                    accessToken: accessToken
                };
            } catch (error) {
                console.error('❌ Failed to parse token:', error);
                sessionStorage.removeItem('google_auth_initiated');
                return {
                    success: false,
                    error: 'Failed to parse authentication token'
                };
            }
        }
        
        // Check for error in callback
        const error = params.get('error');
        if (error) {
            console.error('❌ OAuth error in callback:', error);
            sessionStorage.removeItem('google_auth_initiated');
            sessionStorage.removeItem('auth_return_url');
            
            // Clean up URL
            history.replaceState({}, document.title, '/login');
            
            return {
                success: false,
                error: error
            };
        }
        
        return null;
    }

    performSignIn(resolve, reject) {
        console.log('🔵 Starting Google sign-in process...');
        
        // First try One Tap (doesn't need popup)
        console.log('🔵 Trying Google One Tap (no popup needed)...');
        
        let oneTapShown = false;
        
        // Set up callback for One Tap
        window.google.accounts.id.initialize({
            client_id: this.clientId,
            callback: async (response) => {
                if (response.credential) {
                    console.log('✅ One Tap credential received');
                    oneTapShown = true;
                    
                    // Decode JWT to get user info
                    const payload = this.parseJwt(response.credential);
                    console.log('✅ User info from One Tap:', payload);
                    
                    resolve({
                        success: true,
                        user: {
                            id: payload.sub,
                            name: payload.name,
                            email: payload.email,
                            picture: payload.picture,
                            givenName: payload.given_name,
                            familyName: payload.family_name
                        },
                        idToken: response.credential,
                        accessToken: response.credential
                    });
                }
            },
            auto_select: false,
            cancel_on_tap_outside: false,
            use_fedcm_for_prompt: false
        });
        
        // Try to show One Tap
        window.google.accounts.id.prompt((notification) => {
            console.log('📢 One Tap notification:', notification);
            
            // If One Tap fails, fall back to popup
            if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
                console.log('⚠️ One Tap not available, falling back to popup...');
                console.log('⚠️ Reason:', notification.getNotDisplayedReason ? notification.getNotDisplayedReason() : notification.getSkippedReason());
                
                // Fall back to OAuth popup
                this.performPopupSignIn(resolve, reject);
            }
        });
        
        // Timeout: if One Tap doesn't work in 2 seconds, try popup
        setTimeout(() => {
            if (!oneTapShown) {
                console.log('⏱️ One Tap timeout, trying popup...');
                this.performPopupSignIn(resolve, reject);
            }
        }, 2000);
    }
    
    performPopupSignIn(resolve, reject) {
        console.log('🔵 Using OAuth popup flow...');
        
        // Flag to prevent multiple resolutions
        let resolved = false;
        
        try {
            console.log('⚠️ IMPORTANT: If popup closes immediately, you need to configure Google OAuth.');
            console.log('📋 Add http://localhost:8000 and http://127.0.0.1:8000 to Google Cloud Console.');
            
            const tokenClient = window.google.accounts.oauth2.initTokenClient({
                client_id: this.clientId,
                scope: 'openid profile email',
                ux_mode: 'popup',
                callback: async (tokenResponse) => {
                    // Prevent duplicate processing
                    if (resolved) {
                        console.log('⚠️ Callback already processed, ignoring...');
                        return;
                    }
                    
                    console.log('🟢 Token response received');
                    
                    if (tokenResponse.access_token) {
                        try {
                            const userInfo = await this.getUserInfo(tokenResponse.access_token);
                            console.log('✅ User info fetched:', userInfo);
                            
                            resolved = true;
                            resolve({
                                success: true,
                                user: userInfo,
                                idToken: tokenResponse.access_token,
                                accessToken: tokenResponse.access_token
                            });
                        } catch (error) {
                            console.error('❌ Failed to get user info:', error);
                            resolved = true;
                            resolve({
                                success: false,
                                error: 'Failed to fetch user information'
                            });
                        }
                    } else if (tokenResponse.error) {
                        // Ignore errors if already resolved successfully
                        if (resolved) return;
                        
                        console.error('❌ Token error:', tokenResponse.error);
                        
                        if (tokenResponse.error === 'popup_closed_by_user') {
                            resolved = true;
                            resolve({
                                success: false,
                                error: 'Sign-in cancelled. Please try again.',
                                cancelled: true
                            });
                        } else if (tokenResponse.error === 'popup_failed_to_open') {
                            resolved = true;
                            resolve({
                                success: false,
                                error: 'Popup blocked. Please allow popups and try again.',
                                blocked: true
                            });
                        } else if (tokenResponse.error === 'popup_closed') {
                            // Don't resolve immediately on popup_closed, might still get success
                            console.log('⚠️ Popup closed error, but waiting for potential success callback...');
                        } else {
                            resolved = true;
                            resolve({
                                success: false,
                                error: 'Authentication failed: ' + tokenResponse.error
                            });
                        }
                    }
                },
                error_callback: (error) => {
                    // Ignore error callback if already resolved
                    if (resolved) return;
                    
                    console.error('❌ OAuth error callback (ignoring if success already occurred):', error);
                    
                    // Wait a bit before resolving in case success callback comes
                    setTimeout(() => {
                        if (!resolved) {
                            console.error('📋 This usually means Google OAuth needs to be configured with authorized origins.');
                            console.error('📋 Add http://localhost:8000 and http://127.0.0.1:8000 to Google Cloud Console.');
                            
                            resolved = true;
                            resolve({
                                success: false,
                                error: 'OAuth configuration needed. Check console for details.',
                                config_needed: true
                            });
                        }
                    }, 500);
                }
            });
            
            console.log('🔵 Opening sign-in popup...');
            tokenClient.requestAccessToken({ prompt: 'consent' });
            
        } catch (error) {
            console.error('❌ Failed to initialize OAuth:', error);
            resolve({
                success: false,
                error: 'Failed to initialize Google Sign-In: ' + error.message
            });
        }
    }

    async getUserInfo(accessToken) {
        const response = await fetch(`https://www.googleapis.com/oauth2/v2/userinfo?access_token=${accessToken}`);
        const userInfo = await response.json();
        return {
            id: userInfo.id,
            name: userInfo.name,
            email: userInfo.email,
            picture: userInfo.picture,
            givenName: userInfo.given_name,
            familyName: userInfo.family_name
        };
    }

    parseJwt(token) {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    }

    async signOut() {
        try {
            if (!this.isInitialized) return { success: true };
            
            // Sign out from Google Identity Services
            if (window.google && window.google.accounts && window.google.accounts.id) {
                window.google.accounts.id.disableAutoSelect();
            }
            
            return { success: true };
        } catch (error) {
            console.error('Google sign-out failed:', error);
            return { success: false, error: error.message };
        }
    }

    isSignedIn() {
        // For the new Google Identity Services, we'll track this locally
        return this.currentUser !== null;
    }

    getCurrentUser() {
        return this.currentUser;
    }
}

// Export for use in main app
window.GoogleAuth = GoogleAuth;