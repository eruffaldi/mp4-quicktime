# Extraction of Frame Durations from MP4
# - Direct file Access 
# - OpenCV 
# - FFMPEG
#
# by Emanuele Ruffaldi 2017
#
# TODO: stts is in the codec nominal rate
import sys
import os
import struct
from mp4file import Mp4File
from atom import Atom
import numpy as np
try:
    import cv2
except:
    cv2 = None

class Mp4DurationExtractor:
    def __init__(self,mp4,ofp,stream,verbose):
        self.mp4 = mp4
        self.tstream = stream
        self.istream = 0
        self.verbose = verbose
        self.timeunit_hz = 0 # long unsigned time unit per second
        self.duration = 0 # in seconds
        self.ofp = ofp # output filename
        self.verbose = True
        self.found = False
    def run(self):
        """ Process the MP4 """
        self.found  = False
        for a in self.mp4:
            x = self.extract(a)
            if x:
                return True
        return self.found 
    def extract(self,a,s=""):
        children = []   
        if self.verbose:
            print "atom",s,a.type,a.offset()
        if a.type == "elst":
            fp = a._Atom__source_stream
            fp.seek(a.offset(),0)
            v1,n = struct.unpack(">LL",fp.read(8))
            for i in range(0,n):
                if v1 == 1:
                    d,mt =  struct.unpack(">QQ",fp.read(16))
                else:
                    d,mt =  struct.unpack(">LL",fp.read(8))
                media_rate_integer,media_rate_fraction =  struct.unpack(">HH",fp.read(4))
                if self.verbose:
                    print "\telst",d,mt,media_rate_integer,media_rate_fraction
        elif a.type == "mvhd":
            fp = a._Atom__source_stream
            fp.seek(a.offset(),0)
            v1 = struct.unpack(">L",fp.read(4))[0]
            if self.verbose:
                print a.type,"version",v1
            if v1 == 1:
                created_t,modified_t = struct.unpack(">QQ",fp.read(16))
                tss = 8
            else:
                created_t,modified_t = struct.unpack(">LL",fp.read(8))
                tss = 4
            self.timeunit_hz = struct.unpack(">L",fp.read(4))[0]
            if self.verbose:
                print a.type,"timebase (Hz)",self.timeunit_hz
            if v1 == 1:
                self.duration = struct.unpack(">Q",fp.read(8))[0]
                tss = 8
            else:
                self.duration = struct.unpack(">L",fp.read(4))[0]
                tss = 4
            self.rate = struct.unpack(">H",fp.read(2))[0]
            if self.verbose:
                print a.type,"duration (units)",self.duration   
                print a.type,"duration (s)",self.duration/float(self.timeunit_hz)
                print a.type,"playback rate",self.rate   
        elif a.type == "mdhd":
            fp = a._Atom__source_stream
            fp.seek(a.offset(),0)
            v1 = struct.unpack(">L",fp.read(4))[0]
            if self.verbose:
                print a.type,"version",v1
            if v1 == 1:
                created_t,modified_t = struct.unpack(">QQ",fp.read(16))
                tss = 8
            else:
                created_t,modified_t = struct.unpack(">LL",fp.read(8))
                tss = 4
            self.track_timeunit_hz = struct.unpack(">L",fp.read(4))[0]
            if self.verbose:
                print a.type,"track timebase (Hz)",self.track_timeunit_hz
            if v1 == 1:
                self.track_duration = struct.unpack(">Q",fp.read(8))[0]
                tss = 8
            else:
                self.track_duration = struct.unpack(">L",fp.read(4))[0]
                tss = 4
            self.track_rate = struct.unpack(">H",fp.read(2))[0]
            if self.verbose:
                print a.type,"track duration (units)",self.track_duration   
                print a.type,"track duration (s)",self.track_duration/float(self.track_timeunit_hz)
                print a.type,"track playback rate",self.track_rate           
        elif a.type == "stts":
            #ISO/IEC 14496-12 Section 8.15.2.1 Definition
            #http://l.web.umkc.edu/lizhu/teaching/2016sp.video-communication/ref/mp4.pdf
            if self.verbose:
                print "found atom stts"
            fp = a._Atom__source_stream
            fp.seek(a.offset(),0)
            # 4bytes=0
            # uint32 entries
            # entry[entries] as: duration (in base units), count
           
            v1,n= struct.unpack(">LL",fp.read(8))
            dt = np.dtype(">i4")
            pi = np.reshape(np.fromfile(fp,dtype=dt,count=n*2),(n,2))
            pd = pi.astype(np.float64)
            pd[:,1] *= (1.0/(self.track_timeunit_hz))  # Note asumption of 30Hz
            tot = np.sum(pi[:,0])
            dur = np.sum(pi[:,0] * pd[:,1])
            out = np.zeros((tot,1),dtype=np.float64)
            k = 0
            for i in range(0,pd.shape[0]):
                w = int(pd[i,0])
                out[k:k+w] = pd[i,1]
                k += w
            if self.verbose:
                print "estimated duration from expanded (s)",np.sum(out)
                print "estimated duration from sum (s)",dur
            if self.istream == self.tstream:
                np.savetxt(open(self.ofp,"wb"),out)
                print "emitted stream",self.istream
            else:
                print "skipped stream",self.istream
            self.istream += 1
            self.found  = True
            # continue for printing
            return False
        elif a.type != "mdat":
            for child in a:
                if type(child) is Atom:
                    if self.extract(child,s+"-"):
                        return True
            return False

def main():
    import argparse 

    parser = argparse.ArgumentParser(description='MP4 Duration')
    parser.add_argument("input")
    parser.add_argument("outputpath")
    parser.add_argument("--verbose",action="store_true")
    parser.add_argument("--stream",type=int,default=0)
    parser.add_argument("--mode",default="mp4",choices=("mp4","opencv","ffmpeg"))

    args = parser.parse_args()
    path = args.input
    outpath = args.outputpath
    mode = args.mode

    if os.path.isfile(path):
        path,x = os.path.split(path)
        paths = [x]
    else:
        paths = os.listdir(path) 
    print "processing",len(paths),"in",path
    for x in paths:
        fp = os.path.join(path,x)
        ofp = os.path.join(outpath,x+".time")
        if x.endswith(".mp4"):
            #if os.path.isfile(ofp):
            #    continue
            print "doing",fp
            if mode == "opencv":
                if cv2 is None:
                    print "OpenCV not available"
                    continue
                try:
                    cap = cv2.VideoCapture(fp)
                except:
                    print "bad",fp
                    continue
                out = open(ofp+".tmp","w")
                iframe = 1
                while True:
                    ret, frame = cap.read()
                    if ret == 0:
                        break
                    now = cap.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
                    out.write("%d %d\n" % (iframe,now))
                    iframe = iframe + 1
                    if (iframe % 10000) == 0:
                        print "\t",iframe
                # transactional
                os.rename(ofp+".tmp",ofp)
                print "done",x
                out.close()
                cap.release()
            elif mode == "ffmpeg":      
                print "ffmpeg mode",x          
                os.system("ffprobe -i \"%s\" -show_frames -show_entries frame=pkt_pts_time -of csv=p=0 > \"%s\"" % (fp,ofp+".tmp"))
                os.rename(ofp+".tmp",ofp)
                print "done",x
            elif mode == "mp4":
                mp4file = Mp4File( fp )
                ee = Mp4DurationExtractor(mp4file,ofp+".tmp",args.stream,args.verbose)
                if ee.run():
                    print "run"
                    os.rename(ofp+".tmp",ofp)
            else:
                print "Unknown mode",mode
if __name__ == '__main__':
    main()