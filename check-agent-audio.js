// Debug script to add to browser console when agent is connected

// Check if agent has published audio tracks
function checkAgentAudio() {
    const room = window.room; // Assuming room is global
    if (!room) {
        console.error('No room object found');
        return;
    }
    
    console.log('=== AUDIO DEBUG INFO ===');
    console.log('Room participants:', room.participants.size);
    
    // Find agent participant
    let agentParticipant = null;
    room.participants.forEach((participant, sid) => {
        console.log(`Participant ${participant.identity}:`, {
            sid: sid,
            identity: participant.identity,
            tracks: Array.from(participant.tracks.values()).map(t => ({
                sid: t.sid,
                kind: t.kind,
                source: t.source,
                muted: t.muted,
                subscribed: t.subscribed
            }))
        });
        
        if (participant.identity.startsWith('agent-')) {
            agentParticipant = participant;
        }
    });
    
    if (agentParticipant) {
        console.log('\n=== AGENT DETAILS ===');
        console.log('Agent identity:', agentParticipant.identity);
        console.log('Agent tracks:', agentParticipant.tracks.size);
        
        // Check for audio tracks
        const audioTracks = Array.from(agentParticipant.tracks.values()).filter(t => t.kind === 'audio');
        console.log('Agent audio tracks:', audioTracks.length);
        
        audioTracks.forEach((track, index) => {
            console.log(`Audio track ${index}:`, {
                sid: track.sid,
                source: track.source,
                muted: track.muted,
                subscribed: track.subscribed,
                mediaStreamTrack: track.mediaStreamTrack,
                enabled: track.mediaStreamTrack?.enabled
            });
            
            // Check if track has audio activity
            if (track.mediaStreamTrack) {
                const audioContext = new AudioContext();
                const source = audioContext.createMediaStreamSource(new MediaStream([track.mediaStreamTrack]));
                const analyser = audioContext.createAnalyser();
                source.connect(analyser);
                
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(dataArray);
                
                const avgVolume = dataArray.reduce((a, b) => a + b) / dataArray.length;
                console.log(`Track ${index} audio level:`, avgVolume);
            }
        });
    } else {
        console.log('No agent participant found');
    }
    
    // Check WebRTC stats
    console.log('\n=== WEBRTC STATS ===');
    room.localParticipant.trackPublications.forEach(async (publication) => {
        if (publication.track && publication.track.sender) {
            const stats = await publication.track.sender.getStats();
            stats.forEach(stat => {
                if (stat.type === 'outbound-rtp' && stat.kind === 'audio') {
                    console.log('Outbound audio stats:', {
                        bytesSent: stat.bytesSent,
                        packetsSent: stat.packetsSent,
                        timestamp: stat.timestamp
                    });
                }
            });
        }
    });
}

// Also check browser audio
function checkBrowserAudio() {
    console.log('\n=== BROWSER AUDIO CHECK ===');
    console.log('Audio context state:', new AudioContext().state);
    console.log('Media devices available:', navigator.mediaDevices ? 'Yes' : 'No');
    
    // Check if any audio is playing
    const audioElements = document.querySelectorAll('audio, video');
    console.log('Audio/video elements found:', audioElements.length);
    audioElements.forEach((el, i) => {
        console.log(`Element ${i}:`, {
            src: el.src,
            paused: el.paused,
            muted: el.muted,
            volume: el.volume,
            readyState: el.readyState
        });
    });
}

// Run checks
checkAgentAudio();
checkBrowserAudio();

// Copy this entire script and paste in browser console when agent is connected