// Discord Quest Helper - Full Version
(function() {
    console.log('%c[Quest Helper] Loading...', 'color: #00ff00; font-weight: bold');
    
    // Wait for Discord to fully load
    let attempts = 0;
    const maxAttempts = 30;
    
    function waitForDiscord() {
        if (window.webpackChunkdiscord_app && document.querySelector('[class*="app"]')) {
            console.log('%c[Quest Helper] Discord loaded, initializing...', 'color: #00ff00');
            initializeQuestHelper();
        } else if (attempts < maxAttempts) {
            attempts++;
            console.log(`[Quest Helper] Waiting for Discord... (${attempts}/${maxAttempts})`);
            setTimeout(waitForDiscord, 1000);
        } else {
            console.error('[Quest Helper] Failed to load Discord');
        }
    }
    
    function initializeQuestHelper() {
        try {
            // Store original functions
            delete window.$;
            
            // Get Webpack modules
            let wpRequire = webpackChunkdiscord_app.push([[Symbol()], {}, r => r]);
            webpackChunkdiscord_app.pop();
            
            // Find required stores
            let ApplicationStreamingStore = Object.values(wpRequire.c).find(x => x?.exports?.A?.__proto__?.getStreamerActiveStreamMetadata)?.exports?.A;
            let RunningGameStore = Object.values(wpRequire.c).find(x => x?.exports?.Ay?.getRunningGames)?.exports?.Ay;
            let QuestsStore = Object.values(wpRequire.c).find(x => x?.exports?.A?.__proto__?.getQuest)?.exports?.A;
            let ChannelStore = Object.values(wpRequire.c).find(x => x?.exports?.A?.__proto__?.getAllThreadsForParent)?.exports?.A;
            let GuildChannelStore = Object.values(wpRequire.c).find(x => x?.exports?.Ay?.getSFWDefaultChannel)?.exports?.Ay;
            let FluxDispatcher = Object.values(wpRequire.c).find(x => x?.exports?.h?.__proto__?.flushWaitQueue)?.exports?.h;
            let api = Object.values(wpRequire.c).find(x => x?.exports?.Bo?.get)?.exports?.Bo;
            
            if (!QuestsStore || !api) {
                console.error('[Quest Helper] Failed to find required modules');
                return;
            }
            
            console.log('%c[Quest Helper] Modules loaded successfully', 'color: #00ff00');
            
            // Your existing quest completion logic here
            const supportedTasks = ["WATCH_VIDEO", "PLAY_ON_DESKTOP", "STREAM_ON_DESKTOP", "PLAY_ACTIVITY", "WATCH_VIDEO_ON_MOBILE"];
            
            let quests = [...QuestsStore.quests.values()].filter(x => 
                x.userStatus?.enrolledAt && 
                !x.userStatus?.completedAt && 
                new Date(x.config.expiresAt).getTime() > Date.now() && 
                supportedTasks.find(y => Object.keys((x.config.taskConfig ?? x.config.taskConfigV2).tasks).includes(y))
            );
            
            let isApp = typeof DiscordNative !== "undefined";
            
            if (quests.length === 0) {
                console.log('%c[Quest Helper] No active quests found!', 'color: #ffff00');
                return;
            }
            
            console.log(`%c[Quest Helper] Found ${quests.length} active quest(s)`, 'color: #00ff00');
            
            // Process quests sequentially
            let doJob = function() {
                const quest = quests.pop();
                if (!quest) {
                    console.log('%c[Quest Helper] All quests completed!', 'color: #00ff00');
                    return;
                }
                
                console.log(`%c[Quest Helper] Processing: ${quest.config.messages.questName}`, 'color: #00ffff');
                
                const pid = Math.floor(Math.random() * 30000) + 1000;
                const applicationId = quest.config.application.id;
                const applicationName = quest.config.application.name;
                const questName = quest.config.messages.questName;
                const taskConfig = quest.config.taskConfig ?? quest.config.taskConfigV2;
                const taskName = supportedTasks.find(x => taskConfig.tasks[x] != null);
                const secondsNeeded = taskConfig.tasks[taskName].target;
                let secondsDone = quest.userStatus?.progress?.[taskName]?.value ?? 0;
                
                // Handle different quest types
                if (taskName === "WATCH_VIDEO" || taskName === "WATCH_VIDEO_ON_MOBILE") {
                    handleVideoQuest(quest, secondsNeeded, secondsDone, api, doJob);
                } else if (taskName === "PLAY_ON_DESKTOP") {
                    handlePlayQuest(quest, applicationId, applicationName, pid, secondsNeeded, secondsDone, isApp, api, RunningGameStore, FluxDispatcher, doJob);
                } else if (taskName === "STREAM_ON_DESKTOP") {
                    handleStreamQuest(quest, applicationId, pid, secondsNeeded, secondsDone, isApp, ApplicationStreamingStore, FluxDispatcher, doJob);
                } else if (taskName === "PLAY_ACTIVITY") {
                    handleActivityQuest(quest, secondsNeeded, ChannelStore, GuildChannelStore, api, doJob);
                }
            };
            
            // Start processing
            doJob();
            
        } catch (error) {
            console.error('[Quest Helper] Error:', error);
        }
    }
    
    // Helper functions for each quest type
    function handleVideoQuest(quest, secondsNeeded, secondsDone, api, callback) {
        const maxFuture = 10, speed = 7, interval = 1;
        const enrolledAt = new Date(quest.userStatus.enrolledAt).getTime();
        let completed = false;
        
        let fn = async () => {
            while(true) {
                const maxAllowed = Math.floor((Date.now() - enrolledAt)/1000) + maxFuture;
                const diff = maxAllowed - secondsDone;
                const timestamp = secondsDone + speed;
                
                if(diff >= speed) {
                    const res = await api.post({url: `/quests/${quest.id}/video-progress`, body: {timestamp: Math.min(secondsNeeded, timestamp + Math.random())}});
                    completed = res.body.completed_at != null;
                    secondsDone = Math.min(secondsNeeded, timestamp);
                }
                
                if(timestamp >= secondsNeeded) {
                    break;
                }
                await new Promise(resolve => setTimeout(resolve, interval * 1000));
            }
            
            if(!completed) {
                await api.post({url: `/quests/${quest.id}/video-progress`, body: {timestamp: secondsNeeded}});
            }
            
            console.log(`%c[Quest Helper] Completed: ${quest.config.messages.questName}`, 'color: #00ff00');
            callback();
        };
        
        fn();
        console.log(`%c[Quest Helper] Spoofing video for ${quest.config.messages.questName}`, 'color: #ffff00');
    }
    
    function handlePlayQuest(quest, applicationId, applicationName, pid, secondsNeeded, secondsDone, isApp, api, RunningGameStore, FluxDispatcher, callback) {
        if(!isApp) {
            console.log(`%c[Quest Helper] This quest requires Discord desktop app: ${quest.config.messages.questName}`, 'color: #ff0000');
            callback();
            return;
        }
        
        api.get({url: `/applications/public?application_ids=${applicationId}`}).then(res => {
            const appData = res.body[0];
            const exeName = appData.executables?.find(x => x.os === "win32")?.name?.replace(">","") ?? appData.name.replace(/[\/\\:*?"<>|]/g, "");
            
            const fakeGame = {
                cmdLine: `C:\\Program Files\\${appData.name}\\${exeName}`,
                exeName,
                exePath: `c:/program files/${appData.name.toLowerCase()}/${exeName}`,
                hidden: false,
                isLauncher: false,
                id: applicationId,
                name: appData.name,
                pid: pid,
                pidPath: [pid],
                processName: appData.name,
                start: Date.now(),
            };
            
            const realGames = RunningGameStore.getRunningGames();
            const realGetRunningGames = RunningGameStore.getRunningGames;
            const realGetGameForPID = RunningGameStore.getGameForPID;
            
            RunningGameStore.getRunningGames = () => [fakeGame];
            RunningGameStore.getGameForPID = (pid) => [fakeGame].find(x => x.pid === pid);
            FluxDispatcher.dispatch({type: "RUNNING_GAMES_CHANGE", removed: realGames, added: [fakeGame], games: [fakeGame]});
            
            let fn = data => {
                let progress = quest.config.configVersion === 1 ? data.userStatus.streamProgressSeconds : Math.floor(data.userStatus.progress.PLAY_ON_DESKTOP.value);
                console.log(`[Quest Helper] Progress: ${progress}/${secondsNeeded}`);
                
                if(progress >= secondsNeeded) {
                    console.log(`%c[Quest Helper] Completed: ${quest.config.messages.questName}`, 'color: #00ff00');
                    
                    RunningGameStore.getRunningGames = realGetRunningGames;
                    RunningGameStore.getGameForPID = realGetGameForPID;
                    FluxDispatcher.dispatch({type: "RUNNING_GAMES_CHANGE", removed: [fakeGame], added: [], games: []});
                    FluxDispatcher.unsubscribe("QUESTS_SEND_HEARTBEAT_SUCCESS", fn);
                    
                    callback();
                }
            };
            
            FluxDispatcher.subscribe("QUESTS_SEND_HEARTBEAT_SUCCESS", fn);
            console.log(`%c[Quest Helper] Spoofed game: ${applicationName}. Waiting ${Math.ceil((secondsNeeded - secondsDone) / 60)} minutes...`, 'color: #ffff00');
        });
    }
    
    function handleStreamQuest(quest, applicationId, pid, secondsNeeded, secondsDone, isApp, ApplicationStreamingStore, FluxDispatcher, callback) {
        if(!isApp) {
            console.log(`%c[Quest Helper] This quest requires Discord desktop app: ${quest.config.messages.questName}`, 'color: #ff0000');
            callback();
            return;
        }
        
        let realFunc = ApplicationStreamingStore.getStreamerActiveStreamMetadata;
        ApplicationStreamingStore.getStreamerActiveStreamMetadata = () => ({
            id: applicationId,
            pid,
            sourceName: null
        });
        
        let fn = data => {
            let progress = quest.config.configVersion === 1 ? data.userStatus.streamProgressSeconds : Math.floor(data.userStatus.progress.STREAM_ON_DESKTOP.value);
            console.log(`[Quest Helper] Progress: ${progress}/${secondsNeeded}`);
            
            if(progress >= secondsNeeded) {
                console.log(`%c[Quest Helper] Completed: ${quest.config.messages.questName}`, 'color: #00ff00');
                
                ApplicationStreamingStore.getStreamerActiveStreamMetadata = realFunc;
                FluxDispatcher.unsubscribe("QUESTS_SEND_HEARTBEAT_SUCCESS", fn);
                
                callback();
            }
        };
        
        FluxDispatcher.subscribe("QUESTS_SEND_HEARTBEAT_SUCCESS", fn);
        console.log(`%c[Quest Helper] Spoofed stream: ${quest.config.application.name}. Stream any window in VC for ${Math.ceil((secondsNeeded - secondsDone) / 60)} minutes. Need another person in VC!`, 'color: #ffff00');
    }
    
    function handleActivityQuest(quest, secondsNeeded, ChannelStore, GuildChannelStore, api, callback) {
        const channelId = ChannelStore.getSortedPrivateChannels()[0]?.id ?? 
            Object.values(GuildChannelStore.getAllGuilds()).find(x => x != null && x.VOCAL.length > 0)?.VOCAL[0]?.channel?.id;
        const streamKey = `call:${channelId}:1`;
        
        let fn = async () => {
            console.log(`[Quest Helper] Starting activity quest: ${quest.config.messages.questName}`);
            
            while(true) {
                const res = await api.post({url: `/quests/${quest.id}/heartbeat`, body: {stream_key: streamKey, terminal: false}});
                const progress = res.body.progress.PLAY_ACTIVITY.value;
                console.log(`[Quest Helper] Progress: ${progress}/${secondsNeeded}`);
                
                await new Promise(resolve => setTimeout(resolve, 20 * 1000));
                
                if(progress >= secondsNeeded) {
                    await api.post({url: `/quests/${quest.id}/heartbeat`, body: {stream_key: streamKey, terminal: true}});
                    break;
                }
            }
            
            console.log(`%c[Quest Helper] Completed: ${quest.config.messages.questName}`, 'color: #00ff00');
            callback();
        };
        
        fn();
    }
    
    // Start waiting for Discord
    waitForDiscord();
})();