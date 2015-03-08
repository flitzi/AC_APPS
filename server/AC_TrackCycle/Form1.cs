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
        private readonly string serverfolder = @"D:\Games\Steam\SteamApps\common\assettocorsa\server\"; //not used if acServer.exe is found next to this app
        private readonly List<string> iniLines = new List<string>();
        private readonly List<Tuple<string, int>> tracks = new List<Tuple<string, int>>();
        //private readonly List<string> admins = new List<string>(); //not used, you have to pass the admin password everytime for /next_track and /change_track, e.g. "/next_track <mypassword>" or /change_track <mypassword> spa
        private readonly string next_track, change_track;

        private string logFile = null;
        private int logLength = 0;

        private int cycle;
        private Process serverInstance;

        private delegate void outputRecieved(string output);
        private delegate void clearOutput();

        private bool autoChangeTrack = true;

        public Form1()
        {
            this.InitializeComponent();

            if (File.Exists(Path.Combine(Application.StartupPath, "acServer.exe")))
            {
                this.serverfolder = Application.StartupPath;
            }

            StreamReader sr = new StreamReader(Path.Combine(serverfolder, @"cfg\server_cfg.ini"));

            string line = sr.ReadLine();
            while (line != null)
            {
                if (line.StartsWith("TRACKS=", StringComparison.InvariantCultureIgnoreCase))
                {
                    foreach (string parts in line.Substring(line.IndexOf("=") + 1).Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        string[] part = parts.Split(',');
                        string track = part[0].Trim();
                        int laps = int.Parse(part[1]);
                        this.tracks.Add(new Tuple<string, int>(track, laps));
                    }
                }

                if (line.StartsWith("ADMIN_PASSWORD=", StringComparison.InvariantCultureIgnoreCase))
                {
                    string adminpw = line.Substring(line.IndexOf("=") + 1);
                    this.next_track = "ADMIN COMMAND: /next_track " + adminpw;
                    this.change_track = "ADMIN COMMAND: /change_track " + adminpw;
                }

                this.iniLines.Add(line);

                this.textBoxOutput.AppendText(line + Environment.NewLine);

                line = sr.ReadLine();
            }

            sr.Dispose();

            if (this.tracks.Count == 0)
            {
                MessageBox.Show("No TRACKS in TRACK_CYCLE section found.");
                Application.Exit();
            }
        }

        protected override void OnClosing(CancelEventArgs e)
        {
            this.resetOutput();
            base.OnClosing(e);
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);

            if (this.serverInstance != null)
            {
                this.serverInstance.Kill();
            }
        }

        private void writeOuput(string output)
        {
            if (!string.IsNullOrEmpty(output) && !output.StartsWith("No car with address"))
            {
                this.textBoxOutput.AppendText(output + Environment.NewLine);
                logLength++;

                if (logLength > 50000)
                {
                    this.textBoxOutput.AppendText("Flushing log" + Environment.NewLine);
                    this.resetOutput();
                    this.textBoxOutput.AppendText("Log flushed" + Environment.NewLine);
                    logLength = 0;
                }

                if (this.cycle < this.tracks.Count)
                {
                    this.textBoxCurrentCycle.Text = this.tracks[this.cycle].Item1 + " " + this.tracks[this.cycle].Item2 + " laps";
                }
            }
        }

        private void resetOutput()
        {
            if (this.checkBoxCreateLogs.Checked && !string.IsNullOrEmpty(this.logFile))
            {
                StreamWriter sw = new StreamWriter(this.logFile, true);
                sw.Write(textBoxOutput.Text);
                sw.Close();
                sw.Dispose();
            }
            this.textBoxOutput.Text = string.Empty;
        }

        private void buttonStart_Click(object sender, EventArgs e)
        {
            this.cycle = 0;
            this.StartServer();
        }

        private void StartServer()
        {
            try
            {
                this.resetOutput();

                if (this.serverInstance != null)
                {
                    this.serverInstance.Kill();
                }

                if (this.cycle >= this.tracks.Count)
                {
                    this.cycle = 0;
                }

                StreamWriter sw = new StreamWriter(Path.Combine(this.serverfolder, @"cfg\server_cfg.ini"));
                foreach (string line in this.iniLines)
                {
                    string outLine = line;

                    if (line.StartsWith("TRACK=", StringComparison.InvariantCultureIgnoreCase))
                    {
                        outLine = "TRACK=" + this.tracks[cycle].Item1;
                    }

                    if (line.StartsWith("LAPS=", StringComparison.InvariantCultureIgnoreCase))
                    {
                        outLine = "LAPS=" + this.tracks[cycle].Item2;
                    }

                    sw.WriteLine(outLine);
                }

                sw.Dispose();

                this.serverInstance = new Process();
                this.serverInstance.StartInfo.FileName = Path.Combine(serverfolder, "acServer.exe");
                this.serverInstance.StartInfo.WorkingDirectory = serverfolder;
                this.serverInstance.StartInfo.RedirectStandardOutput = true;
                this.serverInstance.StartInfo.UseShellExecute = false;
                this.serverInstance.StartInfo.CreateNoWindow = true;
                this.serverInstance.OutputDataReceived += process_OutputDataReceived;
                this.serverInstance.Start();
                this.serverInstance.BeginOutputReadLine();

                this.logFile = Path.Combine(this.serverfolder, "log_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + "_" + this.tracks[cycle].Item1 + ".txt");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message + " " + ex.StackTrace);
                this.Close();
            }
        }

        void process_OutputDataReceived(object sender, DataReceivedEventArgs e)
        {
            try
            {
                if (string.IsNullOrEmpty(e.Data))
                {
                    return;
                }

                this.BeginInvoke(new outputRecieved(this.writeOuput), e.Data);

                if (this.autoChangeTrack && e.Data == "HasSentRaceoverPacket, move to the next session")
                {
                    this.cycle++;
                    this.StartServer();
                }

                //this is not secure, someone with the same name can exploit admin rights
                //if (e.Data.StartsWith("Making") && e.Data.EndsWith("admin"))
                //{
                //    admins.Add(e.Data.Replace("Making", "").Replace("admin", "").Trim());
                //}

                //if (e.Data.StartsWith("ADMIN COMMAND: /next_track received from") && admins.Contains(e.Data.Replace("ADMIN COMMAND: /next_track received from", "").Trim()))
                //{
                //    cycle++;
                //    StartServer();
                //}

                if (e.Data.StartsWith(this.next_track))
                {
                    this.cycle++;
                    this.StartServer();
                }

                if (e.Data.StartsWith(this.change_track))
                {
                    string track = e.Data.Substring(this.change_track.Length).Trim();
                    track = track.Substring(0, track.IndexOf(" "));
                    for (int i = 0; i < this.tracks.Count; i++)
                    {
                        if (this.tracks[i].Item1 == track)
                        {
                            this.cycle = i;
                            this.StartServer();
                            break;
                        }
                    }                   
                }
            }
            catch (Exception ex)
            {
                this.BeginInvoke(new outputRecieved(this.writeOuput), ex.Message + " " + ex.StackTrace);
            }
        }

        private void buttonNextTrack_Click(object sender, EventArgs e)
        {
            this.cycle++;
            this.StartServer();
        }

        private void checkBoxAutoChangeTrack_CheckedChanged(object sender, EventArgs e)
        {
            this.autoChangeTrack = this.checkBoxAutoChangeTrack.Checked;
        }
    }
}
