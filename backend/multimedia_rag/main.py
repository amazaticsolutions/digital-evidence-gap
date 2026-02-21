#!/usr/bin/env python3
"""
Main entry point for the Multimedia RAG Engine.

This module provides a CLI interface for the forensic video evidence
analysis system. It supports two main commands:

1. ingest: Upload and process video files from Google Drive
2. query: Search processed evidence using natural language queries

Usage (from backend directory):
    # Ingest a video
    python -m multimedia_rag.main ingest \\
        --gdrive_url "https://drive.google.com/file/d/..." \\
        --cam_id "cam1" \\
        --gps_lat 40.7128 \\
        --gps_lng -74.0060

    # Query the evidence
    python -m multimedia_rag.main query \\
        --q "Show me every instance of the red backpack being dropped"

    # Or run directly from multimedia_rag folder:
    python main.py ingest ...
    python main.py query ...

Environment:
    Requires backend/.env file with:
    - MONGO_INITDB_DATABASE: MongoDB Atlas connection string
    - GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH: Path to service account JSON
"""

import argparse
import json
import sys
import os
from typing import Optional

# Add parent directory to path for running as standalone script
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_current_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Import config first to ensure environment is loaded
from multimedia_rag import config

# Import main functions
from multimedia_rag.ingestion import ingest_video
from multimedia_rag.query import run_query, run_reid, get_frame_ids_from_results, format_results_for_display
from multimedia_rag.ingestion.mongo_store import close_connection


def cmd_ingest(args: argparse.Namespace) -> int:
    """
    Execute the ingest command.
    
    Downloads a video from Google Drive and processes all frames through
    the ingestion pipeline (extract → caption → embed → store).
    
    Args:
        args: Parsed command line arguments containing:
            - gdrive_url: Google Drive URL or file ID
            - cam_id: Camera identifier
            - gps_lat: GPS latitude
            - gps_lng: GPS longitude
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("\n" + "="*60)
    print("MULTIMEDIA RAG ENGINE - VIDEO INGESTION")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  Google Drive URL: {args.gdrive_url}")
    print(f"  Camera ID: {args.cam_id}")
    print(f"  GPS: ({args.gps_lat}, {args.gps_lng})")
    
    try:
        # Validate configuration
        config.validate_config()
        
        # Run ingestion
        frames_processed = ingest_video(
            gdrive_url=args.gdrive_url,
            cam_id=args.cam_id,
            gps_lat=args.gps_lat,
            gps_lng=args.gps_lng
        )
        
        print(f"\n✓ Ingestion complete: {frames_processed} frames processed")
        return 0
        
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        return 1
    except ConnectionError as e:
        print(f"\n✗ Connection error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"\n✗ File not found: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up database connection
        close_connection()


def cmd_query(args: argparse.Namespace) -> int:
    """
    Execute the query command.
    
    Searches the processed evidence using a natural language query,
    scores results for relevance, and optionally runs person re-identification.
    
    Args:
        args: Parsed command line arguments containing:
            - q: The natural language query
            - no_reid: If set, skip re-identification
            - output: Output file path (optional)
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("\n" + "="*60)
    print("MULTIMEDIA RAG ENGINE - EVIDENCE QUERY")
    print("="*60)
    
    print(f"\nQuery: {args.q}")
    
    try:
        # Run the query pipeline
        results = run_query(args.q)
        
        # Get frame IDs for ReID
        frame_ids = get_frame_ids_from_results(results)
        
        # Run ReID if we have results and it's not disabled
        reid_mapping = {}
        if frame_ids and not args.no_reid:
            print("\nRunning person re-identification...")
            try:
                reid_mapping = run_reid(frame_ids)
                
                # Add reid_group to results
                for r in results["results"]:
                    r["reid_group"] = reid_mapping.get(r.get("_id"))
                for r in results["timeline"]:
                    r["reid_group"] = reid_mapping.get(r.get("_id"))
                    
            except Exception as e:
                print(f"  Warning: ReID failed: {e}")
                print("  Continuing without re-identification")
        
        # Format results for display (without binary image data)
        display_results = format_results_for_display(results, include_images=False)
        
        # Print results
        print("\n" + "="*60)
        print("QUERY RESULTS")
        print("="*60)
        
        print(f"\nSummary: {display_results.get('summary', 'No summary')}")
        print(f"Total relevant frames: {display_results.get('total', 0)}")
        
        # Print timeline
        if display_results.get("timeline"):
            print("\n--- CRIME TIMELINE ---")
            for item in display_results["timeline"]:
                reid_info = f" [{item.get('reid_group', 'Unknown')}]" if item.get('reid_group') else ""
                print(f"\n[{item.get('sequence', '?')}] {item.get('cam_id', '?')} @ {item.get('timestamp', '?')}s{reid_info}")
                print(f"    Score: {item.get('score', 0)}/100")
                print(f"    {item.get('explanation', 'No explanation')}")
                print(f"    Video: {item.get('gdrive_url', 'N/A')}")
        
        # Print all results with details
        if display_results.get("results"):
            print("\n--- DETAILED RESULTS (by relevance) ---")
            for i, r in enumerate(display_results["results"], 1):
                reid_info = f" [{r.get('reid_group', 'Unknown')}]" if r.get('reid_group') else ""
                print(f"\n{i}. {r.get('_id', 'unknown')}{reid_info}")
                print(f"   Camera: {r.get('cam_id', '?')}")
                print(f"   Timestamp: {r.get('timestamp', '?')}s")
                print(f"   Score: {r.get('score', 0)}/100")
                print(f"   Relevant: {r.get('relevant', False)}")
                print(f"   Explanation: {r.get('explanation', 'N/A')}")
                print(f"   GPS: ({r.get('gps_lat', '?')}, {r.get('gps_lng', '?')})")
                print(f"   Video URL: {r.get('gdrive_url', 'N/A')}")
        
        # Save to file if output path specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(display_results, f, indent=2)
            print(f"\n✓ Results saved to: {args.output}")
        
        # Print full JSON if verbose
        if args.verbose:
            print("\n--- FULL JSON OUTPUT ---")
            print(json.dumps(display_results, indent=2))
        
        print(f"\n✓ Query complete")
        return 0
        
    except ValueError as e:
        print(f"\n✗ Invalid query: {e}")
        return 1
    except ConnectionError as e:
        print(f"\n✗ Connection error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up database connection
        close_connection()


def main():
    """
    Main entry point for the CLI.
    
    Parses command line arguments and dispatches to the appropriate
    command handler (ingest or query).
    """
    parser = argparse.ArgumentParser(
        description="Multimedia RAG Engine for Forensic Video Evidence Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Ingest a video from Google Drive:
    python main.py ingest \\
        --gdrive_url "https://drive.google.com/file/d/abc123/view" \\
        --cam_id "cam1" \\
        --gps_lat 40.7128 \\
        --gps_lng -74.0060

  Query the evidence:
    python main.py query \\
        --q "Show me every instance of the red backpack being dropped"

  Query with output file:
    python main.py query \\
        --q "Find people entering through back door" \\
        --output results.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest a video file from Google Drive"
    )
    ingest_parser.add_argument(
        "--gdrive_url",
        required=True,
        help="Google Drive URL or file ID of the video"
    )
    ingest_parser.add_argument(
        "--cam_id",
        required=True,
        help="Camera identifier (e.g., 'cam1', 'lobby_cam')"
    )
    ingest_parser.add_argument(
        "--gps_lat",
        type=float,
        required=True,
        help="GPS latitude coordinate of camera location"
    )
    ingest_parser.add_argument(
        "--gps_lng",
        type=float,
        required=True,
        help="GPS longitude coordinate of camera location"
    )
    
    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the evidence with natural language"
    )
    query_parser.add_argument(
        "--q",
        required=True,
        help="Natural language query (e.g., 'Show me the red backpack')"
    )
    query_parser.add_argument(
        "--no_reid",
        action="store_true",
        help="Skip person re-identification"
    )
    query_parser.add_argument(
        "--output",
        "-o",
        help="Output file path for JSON results"
    )
    query_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print full JSON output"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to appropriate command
    if args.command == "ingest":
        return cmd_ingest(args)
    elif args.command == "query":
        return cmd_query(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
