// Test script to simulate Electron IPC flow
const { spawn } = require('child_process');
const path = require('path');

// Simulate what renderer.js does
function simulateFrontend(prompt, tone) {
    console.log('=== Simulating Frontend (renderer.js) ===');
    console.log('Prompt:', prompt);
    console.log('Selected Tone:', tone);
    
    const context = { tone: tone };
    console.log('Context object:', context);
    
    // Simulate what main.js does
    simulateMainProcess(prompt, context);
}

// Simulate what main.js does
function simulateMainProcess(prompt, context) {
    console.log('\n=== Simulating Main Process (main.js) ===');
    console.log('Received Prompt:', prompt);
    console.log('Received Context:', JSON.stringify(context));
    
    const pythonScript = path.join(__dirname, 'text_ai_backend.py');
    const args = [pythonScript, JSON.stringify(prompt)];
    
    if (context && Object.keys(context).length > 0) {
        args.push(JSON.stringify(context));
        console.log('Context passed to Python:', JSON.stringify(context));
    } else {
        console.log('No context provided');
    }
    
    console.log('Python command args:', args);
    console.log('\n=== Calling Python Script ===\n');
    
    const pythonProcess = spawn('python', args, {
        cwd: __dirname,
        shell: true,
        env: process.env
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
        process.stderr.write(data); // Show debug output
    });

    pythonProcess.on('close', (code) => {
        console.log('\n=== Python Process Finished ===');
        if (code === 0) {
            try {
                const result = JSON.parse(output);
                console.log('Result:', result);
                if (result.text) {
                    console.log('\n✅ SUCCESS: Text generated with tone applied!');
                    console.log('Generated Text:', result.text.substring(0, 100) + '...');
                } else {
                    console.log('❌ ERROR: No text in result');
                }
            } catch (e) {
                console.log('❌ ERROR: Failed to parse Python output:', output);
            }
        } else {
            console.log('❌ ERROR: Python script error:', errorOutput);
        }
    });
}

// Test cases
console.log('🧪 Testing Flow with Different Tones\n');
console.log('='.repeat(60));

// Test 1: Casual tone
setTimeout(() => {
    console.log('\n📝 TEST 1: Casual Tone');
    console.log('-'.repeat(60));
    simulateFrontend('Write a short greeting', 'casual');
}, 100);

// Test 2: Formal tone
setTimeout(() => {
    console.log('\n\n📝 TEST 2: Formal Tone');
    console.log('-'.repeat(60));
    simulateFrontend('Write a short greeting', 'formal');
}, 5000);

// Test 3: Professional tone
setTimeout(() => {
    console.log('\n\n📝 TEST 3: Professional Tone');
    console.log('-'.repeat(60));
    simulateFrontend('Write a short greeting', 'professional');
}, 10000);
