using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AC_TrackCycle
{
    public partial class Form1 : Form
    {
        private readonly TrackCycler trackCycler;

        private int logLength = 0;

        public Form1()
        {
            this.InitializeComponent();

            string serverfolder = @"D:\Games\Steam\SteamApps\common\assettocorsa\server\"; //not used if acServer.exe is found next to this app
            if (File.Exists(Path.Combine(Application.StartupPath, "acServer.exe")))
            {
                serverfolder = Application.StartupPath;
            }

            this.trackCycler = new TrackCycler(serverfolder);

            if (trackCycler.Sessions.Count == 0)
            {
                MessageBox.Show("No TRACKS in TRACK_CYCLE section found.");
                this.buttonNextTrack.Enabled = this.buttonStart.Enabled = false;
            }
            else
            {
                foreach (RaceSession session in trackCycler.Sessions)
                {
                    this.textBoxOutput.Text += session.ToString() + Environment.NewLine;
                }
            }

            this.trackCycler.AutoChangeTrack = this.checkBoxAutoChangeTrack.Checked;
            this.trackCycler.CreateLogs = this.checkBoxCreateLogs.Checked;

            this.trackCycler.MessageReceived += trackCycler_MessageReceived;
            this.trackCycler.TrackChanged += trackCycler_TrackChanged;
        }

        void trackChanged(RaceSession session)
        {
            this.textBoxCurrentCycle.Text = session.ToString();
        }

        void trackCycler_TrackChanged(RaceSession session)
        {
            BeginInvoke(new TrackChanged(trackChanged), session);
        }

        void messageReceived(string message)
        {
            if (logLength > 50000)
            {
                this.textBoxOutput.Text = string.Empty;
                logLength = 0;
            }

            this.textBoxOutput.AppendText(message + Environment.NewLine);
            logLength++;
        }

        void trackCycler_MessageReceived(string message)
        {
            BeginInvoke(new MessageReceived(messageReceived), message);
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);
            this.trackCycler.StopServer();
        }

        private void buttonStart_Click(object sender, EventArgs e)
        {
            this.trackCycler.StartServer();
        }

        private void buttonNextTrack_Click(object sender, EventArgs e)
        {
            this.trackCycler.NextTrack();
        }

        private void checkBoxAutoChangeTrack_CheckedChanged(object sender, EventArgs e)
        {
            this.trackCycler.AutoChangeTrack = this.checkBoxAutoChangeTrack.Checked;
        }

        private void checkBoxCreateLogs_CheckedChanged(object sender, EventArgs e)
        {
            this.trackCycler.CreateLogs = this.checkBoxCreateLogs.Checked;
        }
    }
}
