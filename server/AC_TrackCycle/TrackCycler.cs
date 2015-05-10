using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;

namespace AC_TrackCycle
{
    public delegate void MessageReceived(string message);
    public delegate void TrackChanged(RaceSession session);

    public class TrackCycler
    {
        private readonly string serverfolder;
        private readonly List<string> iniLines = new List<string>();
        public readonly List<RaceSession> Sessions = new List<RaceSession>();
        //private readonly List<string> admins = new List<string>(); //not used, you have to pass the admin password everytime for /next_track and /change_track, e.g. "/next_track <mypassword>" or /change_track <mypassword> spa
        private readonly string next_trackCommand, change_trackCommand;

        public RaceSession CurrentSession
        {
            get
            {
                return this.Sessions[this.cycle];
            }
        }

        public bool CreateLogs = true;
        private StreamWriter logWriter;

        private int cycle = 0;
        private Process serverInstance;

        public bool AutoChangeTrack = true;

        public event MessageReceived MessageReceived;
        public event TrackChanged TrackChanged;

        public TrackCycler(string serverfolder)
        {
            this.serverfolder = serverfolder;

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
                        string config = string.Empty;
                        if (part.Length == 3)
                        {
                            config = part[1].Trim();
                        }
                        int laps = int.Parse(part[part.Length - 1]);
                        this.Sessions.Add(new RaceSession(track, config, laps));
                    }
                }

                if (line.StartsWith("ADMIN_PASSWORD=", StringComparison.InvariantCultureIgnoreCase))
                {
                    string adminpw = line.Substring(line.IndexOf("=") + 1);
                    this.next_trackCommand = "ADMIN COMMAND: /next_track " + adminpw;
                    this.change_trackCommand = "ADMIN COMMAND: /change_track " + adminpw;
                }

                this.iniLines.Add(line);
                line = sr.ReadLine();
            }
            sr.Dispose();
        }

        public void StartServer()
        {
            if (this.logWriter != null)
            {
                this.logWriter.Close();
                this.logWriter.Dispose();
            }

            this.StopServer();

            if (this.cycle >= this.Sessions.Count)
            {
                this.cycle = 0;
            }

            StreamWriter sw = new StreamWriter(Path.Combine(this.serverfolder, @"cfg\server_cfg.ini"));
            foreach (string line in this.iniLines)
            {
                string outLine = line;

                if (line.StartsWith("TRACK=", StringComparison.InvariantCultureIgnoreCase))
                {
                    outLine = "TRACK=" + this.Sessions[cycle].Track;
                }

                if (line.StartsWith("CONFIG_TRACK=", StringComparison.InvariantCultureIgnoreCase))
                {
                    outLine = "CONFIG_TRACK=" + this.Sessions[cycle].Layout;
                }

                if (line.StartsWith("LAPS=", StringComparison.InvariantCultureIgnoreCase))
                {
                    outLine = "LAPS=" + this.Sessions[cycle].Laps;
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

            if (this.CreateLogs)
            {
                string logFile = Path.Combine(this.serverfolder, "log_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + "_" + this.Sessions[cycle].Track + ".txt");
                this.logWriter = new StreamWriter(logFile, false);
                this.logWriter.AutoFlush = true;
            }

            if (this.TrackChanged != null)
            {
                this.TrackChanged(this.Sessions[this.cycle]);
            }
        }

        private void process_OutputDataReceived(object sender, DataReceivedEventArgs e)
        {
            try
            {
                string message = e.Data;

                if (!string.IsNullOrEmpty(message) && !message.StartsWith("No car with address"))
                {
                    if (MessageReceived != null)
                    {
                        MessageReceived(message);
                    }

                    if (this.logWriter != null)
                    {
                        this.logWriter.WriteLine(message);
                    }

                    if (this.AutoChangeTrack && message == "HasSentRaceoverPacket, move to the next session")
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

                    if (message.StartsWith(this.next_trackCommand))
                    {
                        this.cycle++;
                        this.StartServer();
                    }

                    if (message.StartsWith(this.change_trackCommand))
                    {
                        string track = message.Substring(this.change_trackCommand.Length).Trim();
                        string layout = string.Empty;
                        track = track.Substring(0, track.IndexOf(" "));
                        string[] parts = track.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length == 2)
                        {
                            track = parts[0];
                            layout = parts[1];
                        }
                        for (int i = 0; i < this.Sessions.Count; i++)
                        {
                            if (this.Sessions[i].Track == track && this.Sessions[i].Layout == layout)
                            {
                                this.cycle = i;
                                this.StartServer();
                                break;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                if (MessageReceived != null)
                {
                    MessageReceived(ex.Message + " " + ex.StackTrace + Environment.NewLine);
                }
            }
        }

        public void NextTrack()
        {
            this.cycle++;
            this.StartServer();
        }

        public void StopServer()
        {
            if (this.serverInstance != null)
            {
                this.serverInstance.Kill();
            }
        }
    }

    public class RaceSession
    {
        public readonly string Track, Layout;
        public readonly int Laps;

        public RaceSession(string track, string layout, int laps)
        {
            this.Track = track;
            this.Layout = layout;
            this.Laps = laps;
        }

        public override string ToString()
        {
            if (string.IsNullOrEmpty(this.Layout))
            {
                return this.Track + " " + this.Laps + " laps";
            }
            return this.Track + "," + this.Layout + " " + this.Laps + " laps";
        }
    }
}
