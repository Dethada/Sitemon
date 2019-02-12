#!/usr/bin/env node

/*
 * npm install --save puppeteer valid-url
 */

const puppeteer = require('puppeteer'); // https://stackoverflow.com/a/24638042
const validUrl = require('valid-url');
const argv = require('minimist')(process.argv.slice(2));
const url = argv.u
const outputfile = argv.o

// https://stackoverflow.com/a/21273362
if (outputfile == null || url == null ) {
    console.log('Missing argument -u <url> or -o <output filename>');
    process.exit(1);
}

if (!validUrl.isUri(url)){
    console.error('Bad URL');
    process.exit(1);
}

async function run() {
    try {
        const browser = await puppeteer.launch({
            headless: true,
            timeout: 100000
            // args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const page = await browser.newPage();

        page.on('error', msg => {
            throw msg ;
        });

        await page.goto(url, {
            waitUntil: 'networkidle2'
        });

        await page.screenshot({ path: outputfile, fullPage: true });
        await browser.close();
    } catch (err) {
        console.error(err);
    }
}

run();
